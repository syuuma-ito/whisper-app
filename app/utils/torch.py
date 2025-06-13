def can_use_gpu():
    """
    PyTorch が GPU を使用できるかどうかを返す

    Returns:
        bool: GPU が使用可能な場合は True、それ以外は False
    """
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False
