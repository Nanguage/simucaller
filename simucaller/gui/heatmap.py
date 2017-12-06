import numpy as np
from scipy import stats

from simucaller.helpers import get_logger

log = get_logger(__name__)

def zscore_heatmap2d(heatmap2d):
    """
    get 2d heatmap zscore
    """
    mat = heatmap2d
    mat = -np.log10(mat)
    mat[mat == -np.inf] = 0
    zscore = stats.zscore(mat)
    return zscore

def pvalue2zscore(pvalue, heatmap2d_pvalue):
    """
    convert pvalue to zscore in the population of heatmap2d
    """
    log2_p = -np.log10(pvalue)
    mat = -np.log10(heatmap2d_pvalue)
    mat[mat == -np.inf] = 0
    std = mat.std()
    mean = mat.mean()
    zscore = (log2_p - mean) / std
    return zscore

def draw_heatmap(axes, heatmap2d_pvalue, cutoff=None, alpha=0.6):
    """
    draw heatmap on target axes.

    :axes: target axes.
    :heatmap2d: target heatmap
    :cutoff: (float/None) the value lagger than cutoff pvalue will not show.
    :alpha: (float)
    """
    assert 0 <= alpha <= 1
    mat = zscore_heatmap2d(heatmap2d_pvalue)
    if cutoff:
        mat = np.where(heatmap2d_pvalue <= cutoff, mat, np.nan)
    axes.matshow(mat, cmap='YlOrRd', alpha=alpha)
