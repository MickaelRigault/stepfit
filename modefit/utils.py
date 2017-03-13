
#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""This module gather the customed decorators of astrobject"""

import matplotlib.pyplot as mpl

def make_method(obj):
    """Decorator to make the function a method of *obj*.

    In the current context::
      @make_method(Axes)
      def toto(ax, ...):
          ...
    makes *toto* a method of `Axes`, so that one can directly use::
      ax.toto()
    COPYRIGHT: from Yannick Copin
    """

    def decorate(f):
        setattr(obj, f.__name__, f)
        return f

    return decorate

from matplotlib import docstring
def _autogen_docstring_inheritance(base,source_inheritance="Unknown"):
    """Autogenerated wrappers will get their docstring from a base function
    with an addendum."""
    msg ="\n\n[ This function is inheriting %s ]"%source_inheritance
    addendum = docstring.Appender(msg, '\n\n')
    return lambda func: addendum(docstring.copy_dedent(base)(func))

def kwargs_update(default,**kwargs):
    """
    """
    k = default.copy()
    for key,val in kwargs.iteritems():
        k[key] = val
        
    return k

def kwargs_extract(default,**kwargs):
    """
    like kwargs_update but extracts keys of default from kwargs

    Returns:
    k -- dictionary based on default update for kwargs
    l -- kwargs without keys defined in default
    """
    k = default.copy()
    l = {}
    for key,val in kwargs.iteritems():
        if key in k.keys():
            k[key] = val
        else:
            l[key] = val

    return k, l


##############################
#                            #
#   MPL ADDON                #
#                            #
##############################
@make_method(mpl.Axes)
def insert_ax(ax,location,shrunk=0.7,space=.05,
              axspace=0.02,shareax=False,**kwargs):
    """ insert an axis at the requested location

              
    The new axis will share the main axis x-axis (location=top or bottom) or
    the y-axis (location=left or right).

    Parameters:
    -----------
    location: [string]
       top/bottom/left/right, i.e. where new axis will be set

    shrunk: [float]
        the main axis will be reduced by so much (0.7 = 70%).
        the new axis will take the room

    space: [float]
        extra space new axis does not use between it and the edge of
        the figure. (in figure unit, i.e., [0,1])

    axspace: [float]
        extra space new axis does not use between it and the input
        axis. (in figure unit, i.e., [0,1])

    shareax: [bool]
        The new axis will share the main axis x-axis (location=top or bottom) or
        the y-axis (location=left or right). If so, the axis ticks will be cleaned.
                           
    **kwargs goes to figure.add_axes() for the new axis

    Returns:
    --------
    axes (the new axis)
    """
    # --------------------
    # hist x
    # -------------------- #
    # -- keep trace of the original axes
    bboxorig = ax.get_position().frozen()

    if location in ["top","bottom"]:
        axhist = ax.figure.add_axes([0.1,0.2,0.3,0.4],sharex=ax if shareax else None,
                                    **kwargs) # This will be changed
        _bboxax = ax.get_position().shrunk(1,shrunk)
        _bboxhist = Bbox([[_bboxax.xmin, _bboxax.ymax+axspace ],
                          [_bboxax.xmax, bboxorig.ymax-space]])
        
        if location == "bottom":
            tanslate = _bboxhist.height + space+axspace
            _bboxhist = _bboxhist.translated(0, bboxorig.ymin-_bboxhist.ymin+space)
            _bboxax = _bboxax.translated(0,tanslate)
            
    # --------------------
    # hist y
    # -------------------- #            
    elif location in ["right","left"]:
        axhist = ax.figure.add_axes([0.5,0.1,0.2,0.42],sharey=ax if shareax else None,
                                    **kwargs) # This will be changed
        _bboxax = ax.get_position().shrunk(shrunk,1)
        _bboxhist = Bbox([[_bboxax.xmax+axspace, _bboxax.ymin ],
                          [bboxorig.xmax-space, _bboxax.ymax]])
        if location == "left":
            tanslate = _bboxhist.width + space + axspace
            _bboxhist = _bboxhist.translated(bboxorig.xmin-_bboxhist.xmin+space, 0)
            _bboxax = _bboxax.translated(tanslate,0)
        
    else:
        raise ValueError("location must be 'top'/'bottom'/'left' or 'right'")


    axhist.set_position(_bboxhist)
    ax.set_position(_bboxax)

    # ---------------------
    # remove their ticks
    if shareax:
        if location in ["top","right"]:
            [[label.set_visible(False) for label in lticks]
            for lticks in [axhist.get_xticklabels(),axhist.get_yticklabels()]]
        elif location == "bottom":
            [[label.set_visible(False) for label in lticks]
            for lticks in [ax.get_xticklabels(),axhist.get_yticklabels()]]
        elif location == "left":
            [[label.set_visible(False) for label in lticks]
            for lticks in [ax.get_yticklabels(),axhist.get_xticklabels()]]
    
    return axhist
        
# ========================== #
# =  Improved methods      = #
# ========================== #
@make_method(mpl.Axes)
def vline(ax,value,ymin=None,ymax=None,
                **kwargs):
     """ use this to help mpld3 """
     ymin,ymax = _read_bound_(ax.get_ylim(),ymin,ymax)
     ax.plot([value,value],[ymin,ymax],
             scalex=False,scaley=False,
             **kwargs)
     
@make_method(mpl.Axes)      
def hline(ax,value,xmin=None,xmax=None,
                **kwargs):
    """ use this to help mpld3 """
    xmin,xmax = _read_bound_(ax.get_xlim(),xmin,xmax)
    ax.plot([xmin,xmax],[value,value],
            scalex=False,scaley=False,
            **kwargs)

@make_method(mpl.Axes)
def hspan(ax,minvalue,maxvalue,
            xmin=None,xmax=None,
            **kwargs):
    """ use this to help mpld3 """
    lims = ax.get_xlim()
    xmin,xmax = _read_bound_(lims,xmin,xmax)
    ax.fill_betweenx([minvalue,maxvalue],xmax,x2=xmin,
                     **kwargs)
    ax.set_xlim(lims)

@make_method(mpl.Axes)
def vspan(ax,minvalue,maxvalue,ymin=None,ymax=None,
          **kwargs):
    """use this to help mpld3"""
    lims = ax.get_ylim()
    ymin,ymax = _read_bound_(lims,ymin,ymax)
    ax.fill_betweenx([ymin,ymax],[minvalue,minvalue],[maxvalue,maxvalue],
                     **kwargs)
    ax.set_ylim(lims)

    
def _read_bound_(lims,xmin,xmax):
    """
    """
    if xmin is None or xmax is None:
        size = lims[1] - lims[0]
    if xmin is None:
        xmin = lims[0] - size*3
    if xmax is None:
        xmax = lims[1] + size*3
    return xmin,xmax

# ========================== #
# =  Figure Add-on         = #
# ========================== #
@make_method(mpl.Figure)
def figout(fig,savefile=None,show=True,add_thumbnails=False,
           dpi=200):
    """This methods parse the show/savefile to know if the figure
    shall the shown or saved."""
    
    if savefile in ["dont_show","_dont_show_","_do_not_show_"]:
        show = False
        savefile = None

    if savefile is not None:
        if not savefile.endswith(".pdf"):
            extention = ".png" if not savefile.endswith(".png") else ""
            fig.savefig(savefile+extention,dpi=dpi)
            
        if not savefile.endswith(".png"):
            extention = ".pdf" if not savefile.endswith(".pdf") else ""
            fig.savefig(savefile+extention)
            
        if add_thumbnails:
            fig.savefig(savefile+"_thumb"+'.png',dpi=dpi/10.)
            
    elif show:
        fig.canvas.draw()
        fig.show()
        

@make_method(mpl.Figure)
def add_threeaxes(figure,xhist=True,yhist=True,
                  rect=[0.1,0.1,0.8,0.8],
                  shrunk=0.7, space=0, axspace=0.02,
                  **kwargs):
    """ Create an axis using the usual add_axes of matplotlib, but in addition
    add top and left axes if xhist and yhist are True, respectively
    **kwargs goes to mpl.Figure.add_axes()

    Parameters:
    -----------
    shrunk,space,axspace: [floats/2d-float]  the inserting parameters for the
                          histograms (see insert_ax). They could be 1d/float values
                          or 2d-arrays. In the first case, both axis will share the
                          same value, otherwise the first entry will be for x, the
                          second for y
                          
    """
    
    # ================
    # Input Parsing
    # ================ 
    if "__iter__" not in dir(shrunk):
        shrunk = [shrunk,shrunk]
    elif len(shrunk) == 1:
        shrunk = [shrunk[0],shrunk[0]]
    elif len(shrunk)>2:
        raise ValueError("shrunk cannot have more than 2 entries (x,y)")

    if "__iter__" not in dir(space):
        space = [space,space]
    elif len(space) == 1:
        space = [space[0],space[0]]
    elif len(space)>2:
        raise ValueError("space cannot have more than 2 entries (x,y)")
    
    if "__iter__" not in dir(axspace):
        axspace = [axspace,axspace]
    elif len(axspace) == 1:
        axspace = [axspace[0],axspace[0]]
    elif len(axspace)>2:
        raise ValueError("axspace cannot have more than 2 entries (x,y)")

    # ================
    # Axis Creation
    # ================ 
    ax = figure.add_axes(rect,**kwargs)
    # -- x axis
    if xhist:
        axhistx = ax.insert_ax("top", shrunk=shrunk[0],space=space[0],
                            axspace=axspace[0],shareax=True)
    else:
        axhistx = None
    # -- y axis
    if yhist:
        axhisty = ax.insert_ax("right", shrunk=shrunk[1],space=space[1],
                            axspace=axspace[1],shareax=True)
    else:
        axhisty = None
        
    if xhist and yhist:
        axhistx.set_position(axhistx.get_position().shrunk(shrunk[1],1))
        
    return ax,axhistx,axhisty


# --------------------- #
# - Scatter           - #
# --------------------- #
@make_method(mpl.Axes)
def errorscatter(ax,x,y,dx=None,dy=None,**kwargs):
    """
    In Dev
    """
    if dx is None and dy is None:
        return
    prop = kwargs_update({"ls":"None","marker":None,"zorder":2,
                          "ecolor":"0.7"},**kwargs)
    return ax.errorbar(x,y,xerr=dx,yerr=dy,**prop)

# --------------------- #
# - Spectrum          - #
# --------------------- #
@make_method(mpl.Axes)
def specplot(ax,x,y,var=None,
             color=None,bandprop={},
             err_onzero=False,**kwargs):
    """This function in a build-in axes method that enable to quickly and
    easily plot a spectrum.
    """
    # -----------------------
    # - Properties of plot
    default_kwargs = dict(
        color=mpl.cm.Blues(0.8),
        ls="-",lw=1,marker=None,zorder=6,
        )
    if color is not None:
        default_kwargs["color"] = color
    propplot = kwargs_update(default_kwargs,**kwargs)
    # -- Plot 
    pl = ax.plot(x,y,**propplot)
    
    # -----------------------
    # - Properties of band
    if var is not None:
        default_band   = dict(
            color=propplot["color"],alpha=0.3,
            zorder=3,label="_no_legend_"
            )
        bandprop = kwargs_update(default_band,**bandprop)
        # -- Band
        if not err_onzero:
            fill = ax.fill_between(x,y+np.sqrt(var),y-np.sqrt(var),
                            **bandprop)
        else:
            fill = ax.fill_between(x,np.sqrt(var),-np.sqrt(var),
                            **bandprop)
    else:
        fill = None
        
    return pl,fill
