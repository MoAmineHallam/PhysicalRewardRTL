from types import SimpleNamespace as NS
import unittest
from .profile_v2 import attribute_events


class AttributionTests(unittest.TestCase):
    def test_nested_cpu_events_and_device_annotations_are_not_double_counted(self):
        def event(name, own, parent=None, device='CPU', annotation=False):
            return NS(name=name, self_device_time_total=own, cpu_parent=parent,
                      device_type=NS(name=device), is_user_annotation=annotation)
        block = event('block.ffn', 0, annotation=True)
        core = event('ffn.core', 0, block, annotation=True)
        linear = event('aten::linear', 0, core)
        gemm = event('aten::mm', 10, linear)
        norm = event('aten::layer_norm', 3, block)
        gpu_annotation = event('block.ffn', 80, device='CUDA', annotation=True)
        kernel = event('gemm_kernel', 10, device='CUDA')
        result = attribute_events([block, core, linear, gemm, norm, gpu_annotation, kernel])
        self.assertEqual(result['attributed_kernel_us'], 13)
        self.assertEqual(result['region_kernel_us'], {'ffn.core': 10, 'block.ffn': 3})
        self.assertEqual(result['device_activity_us_excluding_annotations'], 10)
        self.assertAlmostEqual(sum(result['region_kernel_fraction'].values()), 1)


if __name__ == '__main__':
    unittest.main()
