import numpy as np
import eh_constants as ehct
import matplotlib.pyplot as plt

# functions for computing the plotted data
def econsfun(r, alg, res):
    """Energy cons (\% of harv)"""
    return res[r][alg][0]/res[r][alg][1]
def errorsfun(r, alg, res):
    """Energy errors (\% of harvested)"""
    return res[r][alg][2]/res[r][alg][1]
def eff_econsfun(r, alg, res):
    """Effective E cons (\% of harv)"""
    return (res[r][alg][0] - (ehct.bmax - res[r][alg][3]))/float(res[r][alg][1])
def finalfun(r, alg, res):
    """Final energy (\% of initial)"""
    return res[r][alg][3]/float(ehct.bmax)

def plot_results(results, with_oracle, saveas=None):
    """
    Plot the results

    results     -- This can be a string, in which case they represent a pickle.
                   Otherwise, they are considered the array of results.
    saveas      -- Suffix to use when saving plots in the current folder.
                   If ignored won't save.
    """
    if type(results) == str:
        try:
            import pickle
            if results.split('.')[0].split('_')[-1] == 'oracle':
                with_oracle = True
            else:
                with_oracle = False
            results = pickle.load(open(results))
        except:
            print "Error loading pickled results"
            return None

    plot_data = {'eff_econsfun':{}, 'errorsfun':{}, 'finalfun':{}}
    algs = ['kansal', 'mallec', 'buchli', 'gorlatova']
    colors = ['0.1', '0.4', '0.7', '1'] # Shades of gray

    # plot
    for fun_idx, fun in enumerate([eff_econsfun, errorsfun, finalfun]):
        if fun_idx == 1:# and with_oracle:
            if with_oracle:
                y_thr = 0.1
            else:
                y_thr = 0.5
            # Special handling for the errors plot
            f, (ax1, ax2) = plt.subplots(2, 1, sharex=True,
                    gridspec_kw={'height_ratios':[3,1]}, num=fun.__name__)
            for alg, algname in enumerate(algs):
                ax1.bar([r + alg*0.2 for r in xrange(7)],
                        [fun(r,alg,results)*100 for r in xrange(7)],
                        width=0.2, color=colors[alg], label=algs[alg])
            ax1.set_ylim([y_thr, 7])
            for alg, algname in enumerate(algs):
                ax2.bar([r + alg*0.2 for r in xrange(7)],
                        [fun(r,alg,results)*100 for r in xrange(7)],
                        width=0.2, color=colors[alg], label=algs[alg])
            ax2.set_ylim([0, y_thr])
            ax2.set_yticks(np.linspace(0.0, y_thr, 2))
            ax2.set_yticklabels(['0', str(y_thr)])
            ax2.tick_params(axis='y', pad=0)
            plt.text(0.02, 0.87, 'Energy errors (\% of harvested)',
                    rotation=90, transform=plt.gcf().transFigure)
            plt.xticks([0.4+r for r in xrange(7)], range(1,8))
            ax1.set_ylim([y_thr, 35])
            ax1.set_yticks(np.linspace(10, 35, 3))
            ax1.set_yticklabels(['10', '20', '30'])
            ax1.legend(loc=1, ncol=2, frameon=True, framealpha=0.5)
            ax2.set_xlabel('Data set')
            plt.tight_layout(pad=1.7, h_pad=-0.6)
            ax1.set_xlim([-0.2,7])
            ax2.set_xlim([-0.2,7])
            if saveas:
                    plt.savefig(fun.__name__+saveas+'.pdf', dpi=150)
            # Done, on to the next
            continue
        plt.figure(fun.__name__)
        for alg in xrange(len(algs)):
            plt.bar([r + alg*0.2 for r in xrange(7)], [fun(r, alg, results)*100 for r in xrange(7)], width=0.2, color=colors[alg], label=algs[alg])
            plot_data[fun.__name__][algs[alg]] = [fun(r, alg, results)*100 for r in xrange(7)]
        plt.legend(loc=1, ncol=2, frameon=True, framealpha=0.5)
        plt.xticks([0.4+r for r in xrange(7)], range(1,8))
        if fun_idx == 0:
            plt.ylim([90,140])
            plt.axhline(100, color='k', linestyle='--')
        #if fun_idx == 1:
        #    plt.legend(frameon=True, framealpha=0.5)
        if fun_idx == 2:
            plt.legend(loc=8, ncol=2)
        #    plt.axhline(100, color='k', linestyle='--')
        #    plt.ylim([90, 135])
        plt.xlabel('Data set')
        plt.ylabel(fun.__doc__)
        plt.xlim([-0.2,7])
        plt.tight_layout()
        if saveas:
                plt.savefig(fun.__name__+saveas+'.pdf', dpi=150)
    return plot_data
