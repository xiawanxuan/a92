-- 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 图像表
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    format VARCHAR(10) NOT NULL CHECK (format IN ('png', 'tiff')),
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_size BIGINT NOT NULL,
    tile_size INTEGER NOT NULL DEFAULT 512,
    num_tiles_x INTEGER NOT NULL,
    num_tiles_y INTEGER NOT NULL,
    total_tiles INTEGER NOT NULL,
    minio_bucket VARCHAR(100) NOT NULL,
    minio_object VARCHAR(255) NOT NULL,
    dzi_bucket VARCHAR(100),
    dzi_object VARCHAR(255),
    upload_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_images_upload_time ON images(upload_time DESC);

-- 图块表
CREATE TABLE tiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    pixel_x INTEGER NOT NULL,
    pixel_y INTEGER NOT NULL,
    UNIQUE(image_id, tile_x, tile_y)
);

CREATE INDEX idx_tiles_image_id ON tiles(image_id);

-- 分类任务表
CREATE TABLE classification_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0,
    processed_tiles INTEGER NOT NULL DEFAULT 0,
    total_tiles INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT
);

CREATE INDEX idx_tasks_status ON classification_tasks(status);
CREATE INDEX idx_tasks_image_id ON classification_tasks(image_id);
CREATE INDEX idx_tasks_start_time ON classification_tasks(start_time DESC);

-- 图块分类结果表
CREATE TABLE tile_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES classification_tasks(id) ON DELETE CASCADE,
    tile_id UUID NOT NULL REFERENCES tiles(id) ON DELETE CASCADE,
    predicted_class VARCHAR(20) NOT NULL
        CHECK (predicted_class IN ('sediment', 'rock', 'coral', 'man_made')),
    confidence FLOAT NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    is_corrected BOOLEAN NOT NULL DEFAULT FALSE,
    corrected_class VARCHAR(20)
        CHECK (corrected_class IN ('sediment', 'rock', 'coral', 'man_made')),
    corrected_at TIMESTAMP,
    corrected_by VARCHAR(100),
    UNIQUE(task_id, tile_id)
);

CREATE INDEX idx_classifications_task_id ON tile_classifications(task_id);
CREATE INDEX idx_classifications_tile_id ON tile_classifications(tile_id);
CREATE INDEX idx_classifications_class ON tile_classifications(predicted_class);

-- 修正记录表
CREATE TABLE correction_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    classification_id UUID NOT NULL REFERENCES tile_classifications(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES classification_tasks(id) ON DELETE CASCADE,
    tile_id UUID NOT NULL REFERENCES tiles(id) ON DELETE CASCADE,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    original_class VARCHAR(20) NOT NULL
        CHECK (original_class IN ('sediment', 'rock', 'coral', 'man_made')),
    new_class VARCHAR(20) NOT NULL
        CHECK (new_class IN ('sediment', 'rock', 'coral', 'man_made')),
    reason TEXT,
    operator VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corrections_classification_id ON correction_records(classification_id);
CREATE INDEX idx_corrections_image_id ON correction_records(image_id);
CREATE INDEX idx_corrections_task_id ON correction_records(task_id);
CREATE INDEX idx_corrections_tile_id ON correction_records(tile_id);
CREATE INDEX idx_corrections_created_at ON correction_records(created_at DESC);

-- Grad-CAM 热力图表
CREATE TABLE grad_cam_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    classification_id UUID NOT NULL REFERENCES tile_classifications(id) ON DELETE CASCADE,
    tile_id UUID NOT NULL REFERENCES tiles(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES classification_tasks(id) ON DELETE CASCADE,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    target_class VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    heatmap_data BYTEA NOT NULL,
    heatmap_width INTEGER NOT NULL,
    heatmap_height INTEGER NOT NULL,
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_width INTEGER,
    bbox_height INTEGER,
    bbox_area_ratio FLOAT,
    bbox_avg_intensity FLOAT,
    bbox_max_intensity FLOAT,
    bbox_confidence FLOAT,
    has_bbox BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_grad_cam_task_id ON grad_cam_results(task_id);
CREATE INDEX idx_grad_cam_tile_id ON grad_cam_results(tile_id);
CREATE INDEX idx_grad_cam_image_id ON grad_cam_results(image_id);
CREATE INDEX idx_grad_cam_classification_id ON grad_cam_results(classification_id);
CREATE INDEX idx_grad_cam_tile_coords ON grad_cam_results(task_id, tile_x, tile_y);
CREATE INDEX idx_grad_cam_confidence ON grad_cam_results(confidence DESC);
CREATE INDEX idx_grad_cam_created_at ON grad_cam_results(created_at DESC);
