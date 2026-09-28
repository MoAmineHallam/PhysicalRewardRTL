"""Explicit configurations for the new screen; old campaigns remain unchanged."""
from .model import Config

ARMS = ('dense', 'dense256', 'dense300', 'grouped', 'communication_gate',
        'communication_value', 'communication_post', 'groupbert_pattern',
        'dense896', 'blockdense', 'blockdense_guided', 'dense232')


def configuration(arm):
    if arm not in ARMS:
        raise ValueError('unknown experiment arm')
    values = dict(init_policy='fan_matched')
    if arm.startswith('dense') and arm != 'dense':
        values['hidden'] = int(arm[5:])
    elif arm == 'grouped':
        values['groups'] = 4
    elif arm.startswith('communication_'):
        values.update(ffn_kind=arm, groups=4, rank=36)
    elif arm == 'groupbert_pattern':
        values.update(ffn_kind=arm, groups=4)
    elif arm.startswith('blockdense'):
        values.update(ffn_kind=arm, factor_blocks=4, rank=96)
    return Config(**values)
