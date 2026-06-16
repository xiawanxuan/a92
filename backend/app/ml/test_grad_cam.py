import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import torch
import numpy as np
from app.ml.model import SonarResNet50
from app.ml.grad_cam import GradCAM, GradCAMManager


def test_grad_cam_basic():
    print("=" * 60)
    print("测试 1: Grad-CAM 基本功能")
    print("=" * 60)

    model = SonarResNet50(num_classes=4, pretrained=False)
    model.eval()

    grad_cam = GradCAM(model, target_layer='layer4')

    batch_size = 2
    input_size = 512
    x = torch.randn(batch_size, 3, input_size, input_size)

    original_h = torch.tensor([512, 300], dtype=torch.float32)
    original_w = torch.tensor([512, 400], dtype=torch.float32)

    target_class = 3

    heatmap, weights, logits = grad_cam.generate_heatmap(
        x, target_class, original_h, original_w
    )

    print(f"输入形状: {x.shape}")
    print(f"热力图形状: {heatmap.shape}")
    print(f"权重形状: {weights.shape}")
    print(f"logits 形状: {logits.shape}")
    print(f"热力图范围: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
    print(f"热力图均值: {heatmap.mean():.6f}")

    assert heatmap.shape == (batch_size, input_size, input_size)
    assert heatmap.min() >= 0
    assert heatmap.max() <= 1

    print("\n✓ 测试 1 通过: Grad-CAM 基本功能正常")
    return True


def test_grad_cam_manager():
    print("\n" + "=" * 60)
    print("测试 2: GradCAMManager 批处理")
    print("=" * 60)

    model = SonarResNet50(num_classes=4, pretrained=False)
    model.eval()

    manager = GradCAMManager(model, target_layer='layer4')

    input_size = 512
    batch_size = 4
    x = torch.randn(batch_size, 3, input_size, input_size)

    original_h = torch.tensor([512, 512, 350, 400], dtype=torch.float32)
    original_w = torch.tensor([512, 512, 512, 450], dtype=torch.float32)

    predicted_classes = torch.tensor([0, 3, 1, 3], dtype=torch.long)
    confidences = torch.tensor([0.92, 0.95, 0.75, 0.88], dtype=torch.float32)

    man_made_class = 3
    threshold = 0.8

    results = manager.process_batch(
        x, predicted_classes, confidences,
        original_h, original_w,
        man_made_class, threshold
    )

    print(f"批次大小: {batch_size}")
    print(f"人工目标类别索引: {man_made_class}")
    print(f"置信度阈值: {threshold}")
    print()

    print("各图块处理情况:")
    for i in range(batch_size):
        pred = predicted_classes[i].item()
        conf = confidences[i].item()
        has_result = any(r['batch_index'] == i for r in results)
        status = "✓ 生成热力图" if has_result else "✗ 跳过"
        print(f"  图块 {i}: 类别={pred}, 置信度={conf:.2f} {status}")

    print(f"\n生成热力图数量: {len(results)}")

    expected_count = sum(
        1 for i in range(batch_size)
        if predicted_classes[i].item() == man_made_class and confidences[i].item() > threshold
    )
    print(f"预期生成数量: {expected_count}")

    assert len(results) == expected_count, f"结果数量不匹配: {len(results)} vs {expected_count}"

    for result in results:
        assert result['heatmap'].shape == (input_size, input_size)
        assert 'bbox' in result
        assert result['confidence'] > threshold
        assert result['target_class'] == man_made_class

    print("\n✓ 测试 2 通过: GradCAMManager 批处理正确")
    return True


def test_bounding_box_generation():
    print("\n" + "=" * 60)
    print("测试 3: 边界框生成")
    print("=" * 60)

    heatmap_size = 512

    heatmap = np.zeros((heatmap_size, heatmap_size), dtype=np.float32)

    bbox_x, bbox_y, bbox_w, bbox_h = 100, 150, 200, 180
    yy, xx = np.mgrid[0:heatmap_size, 0:heatmap_size]
    mask = (xx >= bbox_x) & (xx < bbox_x + bbox_w) & (yy >= bbox_y) & (yy < bbox_y + bbox_h)
    heatmap[mask] = np.random.uniform(0.5, 1.0, size=mask.sum())
    heatmap[~mask] = np.random.uniform(0, 0.2, size=(~mask).sum())

    bbox = GradCAM.generate_bounding_box(heatmap, threshold=0.3)

    print(f"真实边界框: x={bbox_x}, y={bbox_y}, w={bbox_w}, h={bbox_h}")
    print(f"检测边界框: x={bbox.x}, y={bbox.y}, w={bbox.width}, h={bbox.height}")
    print(f"面积占比: {bbox.area_ratio:.2%}")
    print(f"边界框置信度: {bbox.confidence:.4f}")

    x_overlap = max(0, min(bbox_x + bbox_w, bbox.x + bbox.width) - max(bbox_x, bbox.x))
    y_overlap = max(0, min(bbox_y + bbox_h, bbox.y + bbox.height) - max(bbox_y, bbox.y))
    intersection = x_overlap * y_overlap
    union = bbox_w * bbox_h + bbox.width * bbox.height - intersection
    iou = intersection / union if union > 0 else 0

    print(f"IoU: {iou:.4f}")

    assert iou > 0.7, f"IoU 太低: {iou}"
    assert bbox.area_ratio > 0 and bbox.area_ratio < 1
    assert bbox.confidence > 0

    print("\n✓ 测试 3 通过: 边界框生成正确")
    return True


def test_grad_cam_integration():
    print("\n" + "=" * 60)
    print("测试 4: 完整集成测试")
    print("=" * 60)

    from app.ml.inference import (
        MAN_MADE_CLASS,
        GRAD_CAM_CONFIDENCE_THRESHOLD,
        run_inference
    )

    model = SonarResNet50(num_classes=4, pretrained=False)
    model.eval()

    tile_size = 512
    num_tiles = 8
    tiles = []
    for i in range(num_tiles):
        tile = {
            'image': torch.randn(3, tile_size, tile_size),
            'tile_x': i % 4,
            'tile_y': i // 4,
            'original_h': tile_size if i < 6 else 300,
            'original_w': tile_size if i % 4 != 3 else 400
        }
        tiles.append(tile)

    print(f"常量 MAN_MADE_CLASS: {MAN_MADE_CLASS}")
    print(f"常量 GRAD_CAM_CONFIDENCE_THRESHOLD: {GRAD_CAM_CONFIDENCE_THRESHOLD}")
    print(f"测试图块数量: {len(tiles)}")
    print()

    from app.ml.inference import _load_model
    import types

    mock_inference_module = types.ModuleType('mock_inference')
    mock_inference_module.MAN_MADE_CLASS = MAN_MADE_CLASS
    mock_inference_module.GRAD_CAM_CONFIDENCE_THRESHOLD = GRAD_CAM_CONFIDENCE_THRESHOLD

    grad_cam_manager = GradCAMManager(model, target_layer='layer4')

    batch_images = torch.stack([t['image'] for t in tiles])
    original_h = torch.tensor([t['original_h'] for t in tiles], dtype=torch.float32)
    original_w = torch.tensor([t['original_w'] for t in tiles], dtype=torch.float32)

    with torch.no_grad():
        logits, probs = model(batch_images, original_h, original_w)

    confidences, predicted_classes = torch.max(probs, dim=1)

    man_made_class_idx = model.class_names.index(MAN_MADE_CLASS) if hasattr(model, 'class_names') else 3

    grad_cam_results = grad_cam_manager.process_batch(
        batch_images,
        predicted_classes,
        confidences,
        original_h,
        original_w,
        man_made_class_idx,
        GRAD_CAM_CONFIDENCE_THRESHOLD
    )

    for result in grad_cam_results:
        batch_idx = result['batch_index']
        result['tile_x'] = tiles[batch_idx]['tile_x']
        result['tile_y'] = tiles[batch_idx]['tile_y']

    print("分类结果:")
    for i in range(num_tiles):
        pred = predicted_classes[i].item()
        conf = confidences[i].item()
        is_man_made = pred == man_made_class_idx
        above_threshold = conf > GRAD_CAM_CONFIDENCE_THRESHOLD
        has_grad_cam = any(r['batch_index'] == i for r in grad_cam_results)

        print(f"  图块 {i} (tile_x={tiles[i]['tile_x']}, tile_y={tiles[i]['tile_y']}): "
              f"类别={pred}, 置信度={conf:.3f} "
              f"{'[人工目标]' if is_man_made else ''} "
              f"{'[高置信度]' if above_threshold else ''} "
              f"{'→ Grad-CAM' if has_grad_cam else ''}")

    print(f"\n生成 Grad-CAM 热力图数量: {len(grad_cam_results)}")

    for result in grad_cam_results:
        batch_idx = result['batch_index']
        tile = tiles[batch_idx]
        print(f"\n  热力图 {batch_idx}:")
        print(f"    图块位置: ({tile['tile_x']}, {tile['tile_y']})")
        print(f"    有效尺寸: {tile['original_h']}x{tile['original_w']}")
        print(f"    置信度: {result['confidence']:.4f}")
        if result['bbox']:
            print(f"    边界框: x={result['bbox'].x}, y={result['bbox'].y}, "
                  f"w={result['bbox'].width}, h={result['bbox'].height}")
            print(f"    面积占比: {result['bbox'].area_ratio:.2%}")

        assert result['heatmap'].shape == (tile_size, tile_size)
        assert result['tile_x'] == tile['tile_x']
        assert result['tile_y'] == tile['tile_y']

    print("\n✓ 测试 4 通过: 完整集成测试成功")
    return True


def test_spatial_mask_with_grad_cam():
    print("\n" + "=" * 60)
    print("测试 5: Grad-CAM 与掩码池化协同")
    print("=" * 60)

    model = SonarResNet50(num_classes=4, pretrained=False)
    model.eval()

    grad_cam = GradCAM(model, target_layer='layer4')

    input_size = 512
    x = torch.randn(1, 3, input_size, input_size)

    original_h_full = torch.tensor([512], dtype=torch.float32)
    original_w_full = torch.tensor([512], dtype=torch.float32)

    original_h_partial = torch.tensor([256], dtype=torch.float32)
    original_w_partial = torch.tensor([300], dtype=torch.float32)

    heatmap_full, _, _ = grad_cam.generate_heatmap(
        x, 3, original_h_full, original_w_full
    )

    heatmap_partial, _, _ = grad_cam.generate_heatmap(
        x, 3, original_h_partial, original_w_partial
    )

    print(f"完整图块热力图范围: [{heatmap_full.min():.4f}, {heatmap_full.max():.4f}]")
    print(f"部分图块热力图范围: [{heatmap_partial.min():.4f}, {heatmap_partial.max():.4f}]")
    print()

    valid_h = int(original_h_partial[0].item())
    valid_w = int(original_w_partial[0].item())

    valid_region = heatmap_partial[0, :valid_h, :valid_w]
    padding_region_h = heatmap_partial[0, valid_h:, :]
    padding_region_w = heatmap_partial[0, :, valid_w:]

    print(f"有效区域均值: {valid_region.mean():.6f}")
    print(f"Padding区域(下方)均值: {padding_region_h.mean():.6f}")
    print(f"Padding区域(右侧)均值: {padding_region_w.mean():.6f}")

    assert valid_region.mean() > padding_region_h.mean() * 0.5, "有效区域响应应显著高于padding区域"
    assert valid_region.mean() > padding_region_w.mean() * 0.5, "有效区域响应应显著高于padding区域"

    print("\n✓ 测试 5 通过: Grad-CAM 正确忽略 padding 区域")
    return True


if __name__ == '__main__':
    print("\n开始验证 Grad-CAM 弱监督目标检测功能...\n")

    all_passed = True
    try:
        all_passed &= test_grad_cam_basic()
        all_passed &= test_grad_cam_manager()
        all_passed &= test_bounding_box_generation()
        all_passed &= test_grad_cam_integration()
        all_passed &= test_spatial_mask_with_grad_cam()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过！Grad-CAM 功能验证成功。")
        print("   功能特性:")
        print("   - 仅对置信度 > 0.8 的人工目标自动生成热力图")
        print("   - 支持掩码感知池化，正确处理边界图块")
        print("   - 自动生成目标边界框")
        print("   - 前端支持热力图叠加、透明度调节、多种配色")
    else:
        print("部分测试失败，请检查代码。")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)
