import statsmodels.api as sm
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

def power_law_fitting(degree_by_node, x_min=1,
                      ax=plt.subplot, 
                      color='k', 
                      marker='o', 
                      label='none',
                      visualize=True):
    frequency = [ d for node, d in degree_by_node]
    min_ = np.log10(x_min)
    max_ = np.log10(max(frequency)+1) + 1

    bins = np.logspace(min_, max_, 50)
    bins_out = np.insert(bins, 0, 0)
    bin_width = bins - bins_out[:-1]
    plot_data = Counter(np.digitize(frequency, bins))

    # logar
    plot_data = sorted(plot_data.items(), key=(lambda x: x[0]))
    x = [bins[k] for k,v in plot_data]
    y = [v/bin_width[k] for k,v in plot_data]
    y = y/sum(y)

    # fitting with stats model
    alpha = 0.05 # 95% confidence interval
    reg = sm.OLS(np.log10(y), sm.add_constant(np.log10(x))).fit(cov_type="HC3")
    conf_interval = reg.conf_int(alpha)

    def power_law(x, a, b):
        return np.power(10,b)*np.power(x, a)

    coef = reg.params[1]
    if visualize:
        # ax.scatter(np.log10(x), np.log10(y))
        ax.scatter(x, y, edgecolors=color, marker=marker, label=label + rf' ($\alpha={-coef:.2f}$)', s=200, lw=2,
                    facecolors='none', 
                    )
        draw_x = np.arange(0.5, max(x), 0.1)
        draw_y = power_law(draw_x, reg.params[1], reg.params[0])
        ax.plot(draw_x, draw_y, c=color)

        ax.set_xscale('log')
        ax.set_yscale('log')

        # ax.set_xlim(left=x_min-0.5)
        ax.spines[['right', 'top']].set_visible(False)

    return reg, conf_interval
    # return reg.coef_[0], reg.intercept_
