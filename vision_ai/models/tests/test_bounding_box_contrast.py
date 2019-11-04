import torch

import vision_ai


def test_no_boxes():
    bbox_coords = [
        [],
        []
    ]

    pred_xh = torch.zeros(2, 2, 4, 4)
    embeddings_xh = torch.zeros(2, 3, 4, 4)
    assert vision_ai.models.bounding_box_contrast.batch_loss(
        pred_xh,
        embeddings_xh,
        bbox_coords,
        frac_compare=0.5
    ) == 0.0


def test_one_box_same():
    bbox_coords = [
        [(0, 0, 2, 2)],
        [(0, 0, 2, 2)]
    ]

    pred_xh = torch.zeros(2, 2, 4, 4)
    embeddings_xh = torch.zeros(2, 3, 4, 4)
    for i, bboxes in enumerate(bbox_coords):
        x, y, w, h = bboxes[0]
        pred_xh[i, :, x:x+w, y:y+h] = 1
        embeddings_xh[i, :, x:x+w, y:y+h] = torch.Tensor(
            [1, 2, 3]
        ).view(3, 1, 1)

    assert vision_ai.models.bounding_box_contrast.batch_loss(
        pred_xh,
        embeddings_xh,
        bbox_coords,
        frac_compare=1.0
    ) == 1.0

