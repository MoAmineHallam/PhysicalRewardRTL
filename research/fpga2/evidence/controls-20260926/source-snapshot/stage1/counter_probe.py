"""A bounded CUDA memory-counter availability probe; run under ncu separately."""
import torch


def main():
    x = torch.ones(8 * 1024 * 1024, dtype=torch.float32, device='cuda')
    for _ in range(3): x.add_(1)
    torch.cuda.synchronize()
    torch.cuda.cudart().cudaProfilerStart()
    x.add_(1)
    torch.cuda.synchronize()
    torch.cuda.cudart().cudaProfilerStop()
    print('counter probe completed')


if __name__ == '__main__':
    main()
