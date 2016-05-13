#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" This low level module manages the scipy / minuit variation """

import numpy as np
import warnings

from astrobject import BaseObject

try:
    from iminuit import Minuit
    _HASMINUIT = True
except ImportError:
    warnings.warn("iminuit not accessible. You won't be able to use minuit functions", ImportError)
    _HASMINUIT = False


class MCMC( BaseObject ):
    """ Class Gathering the MCMC run output. based on emcee """
    
    # BaseObject global variables
    PROPERTIES         = ["lnprob","freeparameters","runprop",
                          "burnin","properties"]
    SIDE_PROPERTIES    = []
    DERIVED_PROPERTIES = ["sampler","poswalkers"]
    # MCMC global variables
    RUN_PROPERTIES = ["guess","guess_err","nrun","nwalkers"]
    
    # ========================= #
    #   Initialization          #
    # ========================= #
    
    def __init__(self, lnprob, freeparameters,
                 guess=None,guess_err=None):
        """ """
        self._properties["lnprob"] = lnprob
        self._properties["freeparameters"] = freeparameters
        
    # ========================= #
    #   Main Methods            #
    # ========================= #
    def run(self,**kwargs):
            
        """
        **kwargs could be any `properties` entry:
           nrun, nwalkers, guess, guess_err
        """
        try:
            import emcee
        except ImportError:
            raise ImportError("Install emcee first => sudo pip install emcee")
        
        self.setup(**kwargs)
        if not self.is_setup():
            raise AttributeError("At least one of the following proprety has not been setup: nrun, nwalkers, guess, guess_err")
    
        # -- run the mcmc        
        self._derived_properties["sampler"] = emcee.EnsembleSampler(self.nwalkers, self.nparam, self.lnprob)
        _ = self.sampler.run_mcmc(self.poswalkers, self.nrun)

    # ------------ #
    # - SETTER   - #
    # ------------ #
    def setup(self, reset=True,**kwargs):
        """ setup on or several entries. The derived parameters
        have to be reset. Avoid that by setting reset to False"""

        for k,v in kwargs.items():
            if k not in self.properties.keys():
                raise ValueError("unknown property to setup %s"%k)
            if k in ["guess","guess_err"] and len(v) !=self.nparam:
                raise ValueError("'%s' must be a %d-value array (%d given)"%(k,self.nparam, len(v)))
            self.properties[k] = v
            
        # -- you changed the mcmc, the former values are not correct anymore
        if reset:
            self.reset(reset_property=False)
        
    def set_burnin(self, value):
        """ set the burnin value above which the walkers are consistants.
        This is required to access the `samples`"""
        
        if value<0 or value>self.nrun:
            raise ValueError("the mcmc burnin must be greater than 0 and lower than the amount of run.")
        self._properties["burnin"] = value

    def reset(self, reset_property=True):
        """ clean the derived values """
        if reset_property:
            self._properties["properties"]     = None
            
        self._properties["burnin"]             = None
        self._derived_properties["poswalkers"] = None
        self._derived_properties["sampler"]    = None

    # ========================= #
    #   Plot Methods            #
    # ========================= #
    def show_walkers(self,savefile=None, show=True,
                        cwalker=None, cline=None, truths=None, **kwargs):
        """ Show the walker values for the mcmc run.

        Parameters
        ----------

        savefile: [string]
            where to save the figure. if None, the figure won't be saved

        show: [bool]
            If no figure saved, the function will show it except if this is set
            to False

        cwalker, cline: [matplotlib color]
            Colors or the walkers and input values.
        """
        # -- This show the 
        import matplotlib.pyplot as mpl
        from astrobject.utils.mpladdon import figout
        if not self.has_ran():
            raise AttributeError("you must run mcmc first")
        
        fig = mpl.figure(figsize=[7,3*self.nparam])
        # -- inputs
        if cline is None:
            cline = mpl.cm.Blues(0.4,0.8)
        if cwalker is None:
            cwalker = mpl.cm.binary(0.7,0.2)
        
        # -- ploting            
        for i, name, fitted in zip(range(self.nparam), self.freeparameters, self.guess if truths is None else truths):
            ax = fig.add_subplot(self.nparam,1,i+1, ylabel=name)
            _ = ax.plot(np.arange(self.nrun), self.sampler.chain.T[i],
                        color=cwalker,**kwargs)
            
            ax.axhline(fitted, color=cline, lw=2)

        fig.figout(savefile=savefile, show=show)
        

    def show_corner(self, savefile=None, show=True,
                         truths=None,**kwargs):
        """ this matrix-corner plot showing the correlation between the
        parameters.

        Parameters
        ----------
        savefile: [string/None]
            where to save the figure. If None, the plot won't be saved

        show: [bool]
            If the plot is not saved. It is shown except if this is False

        truths: [array]
            Show values as lines through the matrix-axes.
            
        **kwargs goes to corner.corner

        Return
        ------
        Void
        """
        try:
            import corner
        except ImportError:
            raise ImportError("install corner to be able to do this plot => sudo pip install corner.")
        
        from astrobject.utils.mpladdon import figout
        
        fig = corner.corner(self.samples, labels=self.freeparameters, 
                        truths=self.guess if truths is None else truths,
                        show_titles=True,label_kwargs={"fontsize":"xx-large"},**kwargs)

        fig.figout(savefile=savefile, show=show)
        

    # ========================= #
    #   Properties              #
    # ========================= #
    # -----------
    # MCMC base
    @property
    def freeparameters(self):
        """ """
        return self._properties["freeparameters"]

    
    @property
    def nparam(self):
        """ number of free parameters """
        return len(self.freeparameters)

    @property
    def properties(self):
        """ dictionary containing the parameters needed to setup the mcmc run"""
        if self._properties["properties"] is None:
            self._properties["properties"] = {}
            for k in self.RUN_PROPERTIES :
                self._properties["properties"][k] = None
                
        return self._properties["properties"]

    def is_setup(self):
        """ Check if you defined all the run properties """
        for k in self.RUN_PROPERTIES:
            if self.properties[k] is None:
                return False
        return True
    
    @property
    def lnprob(self):
        """ """
        return self._properties["lnprob"]

    # ------------------
    # - MCMC properties
    @property
    def nrun(self):
        """ """
        return self.properties["nrun"]
    
    @property
    def nwalkers(self):
        """ """
        return self.properties["nwalkers"]

    @nwalkers.setter
    def nwalkers(self,value):
        """ define the number of walker """
        if int(value)<2*self.nparam:
            raise ValueError("emcee request to have at least twice more walkers than parameters.")
        
        self.properties["nwalkers"] = int(value)

    @property
    def poswalkers(self):
        if self._derived_properties["poswalkers"] is None:
            self._derived_properties["poswalkers"] = \
              [self.guess + np.random.randn(self.nparam)*self.guess_err
               for i in range(self.nwalkers)]
            
        return self._derived_properties["poswalkers"]
            
    @property
    def guess(self):
        """ """
        return self.properties["guess"]
        
    @property
    def guess_err(self):
        """ """
        return self.properties["guess_err"]

    @property
    def burnin(self):
        return self._properties["burnin"]
    # -------------------
    # - Derived MCMC
    @property
    def sampler(self):
        """ the emcee mcmc sampler """
        return self._derived_properties["sampler"]
    
    def has_ran(self):
        """ return True if you ran 'run_mcmc' """
        return self.sampler is not None

    @property
    def samples(self):
        """ the flatten samplers after burned in removal, see set_mcmc_samples """
        if not self.has_ran():
            raise AttributeError("run mcmc first.")
        if self.burnin is None:
            raise AttributeError("You did not specified the burnin value. see 'set_burnin")
        
        return self.sampler.chain[:, self.burnin:, :].reshape((-1, self.nparam))

    @property
    def derived_values(self):
        """ dictionary of the mcmc derived values with the structure:
           NAME_OF_THE_PARAMETER = 50% pdf
           NAME_OF_THE_PARAMETER.err = [+1sigma, -1sigma]
        
        """
        values = map(lambda v: (v[1], v[2]-v[1], v[1]-v[0]), zip(*np.percentile(self.samples, [16, 50, 84],axis=0)))
        fitout = {}
        for v,name in zip(values, self.freeparameters):
            fitout[name] = v[0]
            fitout[name+".err"] = [v[1],v[2]]
            
        return fitout

    @property
    def derived_bestparam(self):
        """ best parameter best on the mcmc run. see mcmc_fitvalues for associated errors """
        fit = self.derived_values
        return [fit[name] for name in self.freeparameters]
    
    @property
    def derived_bestparam_err(self):
        """ best parameter best on the mcmc run. see mcmc_fitvalues for associated errors """
        fit = self.derived_values
        return [fit[name+".err"] for name in self.freeparameters]
    
# ========================================== #
#                                            #
#  Use the Scipy-Minuit Tricks               #
#                                            #
# ========================================== #
class BaseFitter( BaseObject ):
    """ Mother class for the fitters """

    PROPERTIES         = ["param_input","model","use_minuit"]
    SIDE_PROPERTIES    = []
    DERIVED_PROPERTIES = ["fitvalues","mcmc"]

    
    # ========================= #
    # = Initialization        = #  
    # ========================= #

    # ========================= #
    # = Main Methods          = #  
    # ========================= #
    # ---------------
    # - Da Fit
    def fit(self,use_minuit=None,
            **kwargs):
        """
        fit the data following the model.

        Parameters:
        -----------
        
        use_minuit: [bool/None]
            If None, this will use the object's current *use_minuit* value.
            If bool, this will set the technique used to fit the *model*
            to the *data* and will thus overwrite the existing
            *self.use_minuit* value.
            Minuit is the iminuit library.
            Scipy.minimize is the alterntive technique.
            The internal functions are made such that none of the other function
            the user have access to depend on the choice of fitter technique.
            For instance the fixing value concept (see set_guesses) remains with
            scipy.
                                   
        **kwargs parameter associated values with the shape:
            'parametername'_guess, 'parametername'_fixed, 'parametername'_boundaries 

        Returns:
        --------
        Void, create output model values.
                    
        """
        self.setup_guesses(**kwargs)
        
        if use_minuit is not None:
            self.use_minuit = use_minuit
        # --------------
        # - Run the fit 
        if self.use_minuit:
            self._fit_minuit_()
        else:
            self._fit_scipy_()
        # -----------------
        # - Read out param
        self._fit_readout_()

    # --------------------- #
    # -- Da Model        -- #
    def set_model(self,model,**kwargs):
        """ Load a BaseModel to the fitter.

        Parameters
        -----------
        model: [modefit.BaseModel]
            model use to fit the data. This model must inherit from the mother
            model class BaseModel.

        **kwargs goes to self.set_guesses.
           (Define the guess, fixed and boundaries values)
           
        Returns
        -------
        Void, defines model and associated objects
        """
        self._properties["model"] = model
        try:
            self.model.get_chi2 = self.get_modelchi2
        except:
            raise ValueError(" You must define a 'get_modelchi2()' method in your fitter.")
        self.setup_guesses(**kwargs)

    
    # --------------------- #
    # -- Ouput Returns   -- #
    # --------------------- #
    def get_fitvalues(self):
        """
        """
        if not self.has_fit_run():
            raise AttributeError("You should fit first !")
        return self.fitvalues.copy()

    def get_fval(self):
        """
        """
        if not self.has_fit_run():
            raise AttributeError("You should fit first !")
        
        if self.use_minuit:
            return self.minuit.fval
        return self.scipy_output['fun']

    def converged_on_boundaries(self):
        """Check if any parameter have converged on any boundary of the model"""
        
        if not self.has_fit_run():
            raise AttributeError("You should fit first !")

        for name in self.model.freeparameters:
            lowerbound,higherbound = eval("self.model.%s_boundaries"%name)
            if lowerbound is not None and \
              "%.4e"%self.fitvalues[name] == "%.4e"%lowerbound :
                return True
            if higherbound is not None and \
              "%.4e"%self.fitvalues[name] == "%.4e"%higherbound :
                return True
        return False

    def is_fit_good(self):
        return self.fitOk and not self.converged_on_boundaries()
        
        
    # ========================= #
    # = Main Methods          = #
    # ========================= #
    def setup_guesses(self,**kwargs):
        """ Defines the guesses, boundaries and fixed values
        that will be passed to the given model.

        For each variable `v` of the model (see model.freeparameters)
        the following array will be defined and set to param_input:
           * v_guess,
           * v_boundaries,
           * v_fixed.
        Three arrays (self.paramguess, self.parambounds,self.paramfixed)
        will be accessible that will point to the defined array.

        Parameter
        ---------
        **kwargs the v_guess, v_boundaries and, v_fixed for as many
        `v` (from the model.freeparameter list).
        All the non-given `v` values will be filled either by pre-existing
        values in the model or with: 0 for _guess, False for _fixed, and
        [None,None] for _boundaries

        Return
        ------
        Void, defines param_input (and consquently paramguess, parambounds and paramfixed)
        """
        def _test_it_(k,info):
            param = k.split(info)[0]
            if param not in self.model.freeparameters:
                raise ValueError("Unknown parameter %s"%param)

        # -- In there, all the model already has
        if not self.is_input_set():
            self._properties['param_input'] = self.model.get_set_param_input()
        
        # -- Then, whatever you gave
        for k,v in kwargs.items():
            if "_guess" in k:
                _test_it_(k,"_guess")
            elif "_fixed" in k:
                _test_it_(k,"_fixed")
            elif "_boundaries" in k:
                _test_it_(k,"_boundaries")
            else:
                raise ValueError("I am not able to parse %s ; not _guess, _fixed nor _boundaries"%k)
            self.param_input[k] = v

        # -- Finally if no values have been set, let's do it
        for name in self.model.freeparameters:
            if name+"_guess" not in self.param_input.keys():
                self.param_input[name+"_guess"] = 0
            if name+"_fixed" not in self.param_input.keys():
                self.param_input[name+"_fixed"] = False
            if name+"_boundaries" not in self.param_input.keys():
                self.param_input[name+"_boundaries"] = [None,None]
            # -- and give it to the model
        self.model.set_param_input(self.param_input)
            #for v in ["_guess","_fixed","_boundaries"]:
            #    self.model.__dict__[name+v] = self.param_input[name+v]

    # ------------------- #
    # - Bayes & MCMC    - #
    # ------------------- #
    def run_mcmc(self,nrun=2000, walkers_per_dof=3,
                 init=None,init_err=None):
        """ run mcmc from the emcee python code. This might take time

        Parameters
        ----------
        nrun: [int]
            number of step run the walkers are going to do.

        walkers_per_dof: [int/float]
            number of walker by degree of freedom (int of nparameter*this used)
            walkers_per_dof should be greater than 2.
        
        Returns
        -------
        Void (fill the self.mcmc property)
        """
        self._derived_properties["mcmc"] = MCMC(self.model.lnprob, self.model.freeparameters)
        
        guess = np.asarray([self.fitvalues[name] for name in self.model.freeparameters]) \
                     if init is None else np.asarray(init)
        guess_err =  np.asarray([self.fitvalues[name+".err"]
                               for name in self.model.freeparameters]) \
                    if init_err is None else np.asarray(init_err)
                               
        self.mcmc.setup(nrun=nrun,nwalkers = walkers_per_dof * self.model.nparam,
                              guess=guess,guess_err = guess_err)

        self.mcmc.run()

    def set_mcmc_burnin(self, burnin):
        """ set the burnin value above which the walkers are consistants.
        This is required to access the `samples`
        """
        self.mcmc.set_burnin(burnin)


    # ==================== #
    # = Ploting Methods  = #
    # ==================== #        
    def show_mcmc_corner(self, savefile=None, show=True,
                         truths=None,**kwargs):
        """ this matrix-corner plot showing the correlation between the
        parameters.

        Parameters
        ----------
        savefile: [string/None]
            where to save the figure. If None, the plot won't be saved

        show: [bool]
            If the plot is not saved. It is shown except if this is False

        truths: [array]
            Show values as lines through the matrix-axes.
            
        **kwargs goes to corner.corner

        Return
        ------
        Void
        """
        self.mcmc.show_corner(savefile=savefile, show=show,
                            truths=truths,**kwargs)
        
    def show_mcmcwalkers(self, savefile=None, show=True,
                        cwalker=None, cline=None, truths=None, **kwargs):
        """ Show the walker values for the mcmc run.

        Parameters
        ----------

        savefile: [string]
            where to save the figure. if None, the figure won't be saved

        show: [bool]
            If no figure saved, the function will show it except if this is set
            to False

        cwalker, cline: [matplotlib color]
            Colors or the walkers and input values.
        """
        self.mcmc.show_walkers(savefile=savefile, show=show,
                        cwalker=cwalker, cline=cline, truths=truths, **kwargs)
    


        
    # ====================== #
    # = Properties         = #
    # ====================== #
    # -------------
    # - Model
    @property
    def model(self):
        """ This model-object used to fit the data """
        return self._properties["model"]
    
    def is_model_set(self):
        """ Test if the model has been set. True means yes """
        return self._properties["model"] is not None
    
    # -----------------------
    # - fit associated values
    @property
    def fitvalues(self):
        """ dictionary containing the best-fitted values """
        if self._derived_properties["fitvalues"] is None:
            self._derived_properties["fitvalues"] = {}
        return self._derived_properties["fitvalues"]

    def has_fit_run(self):
        return len(self.fitvalues.keys())>0

    @property
    def use_minuit(self):
        if self._properties["use_minuit"] is None:
            warnings.warn("No value set for 'use_minuit' => True is set by default")
            self._properties["use_minuit"] = True
        return self._properties["use_minuit"]
    
    @use_minuit.setter
    def use_minuit(self,use_minuit_bool):
        """ set the use_minuit value """
        self._properties["use_minuit"] = bool(use_minuit_bool)
        
    # -----------------------
    # - Parameters Values
    @property
    def param_input(self):
        """ dictionnary containing the input parameter values:
           guess / fixed / bounds

        See also the respective class properties
        """
        if self._properties["param_input"] is None:
            self._properties["param_input"] = {}
        return self._properties["param_input"]
    
    def is_input_set(self):
        """ Test if you set the parameters inputs """
        return len(self.param_input.keys())>0
    
    @property
    def paramguess(self):
        """ guess put for the fit """
        return [self.param_input["%s_guess"%name]
                for name in self.model.freeparameters]
    @property
    def parambounds(self):
        """ guess put for the fit """
        return [self.param_input["%s_bounds"%name]
                for name in self.model.freeparameters]
        
    @property
    def paramfixed(self):
        """ guess put for the fit """
        return [self.param_input["%s_fixed"%name]
                for name in self.model.freeparameters]

    # ---------------
    # - MCMC Stuffs  
    @property
    def mcmc(self):
        """ MCMC class containing the mcmc parameters """
        return self._derived_properties["mcmc"]

    def has_mcmc(self):
        """ return True if you ran 'run_mcmc' """
        return self.mcmc is not None
    
    @property
    def mcmc_samples(self):
        """ the flatten samplers after burned in removal, see set_mcmc_samples """
        if not self.has_mcmc():
            raise AttributeError("run mcmc first.")
        return self.mcmc.samples

    @property
    def mcmc_fitvalues(self):
        """ dictionary of the mcmc derived values with the structure:
           NAME_OF_THE_PARAMETER = 50% pdf
           NAME_OF_THE_PARAMETER.err = [+1sigma, -1sigma]
        
        """
        if not self.has_mcmc():
            raise AttributeError("run mcmc first.")
        return self.mcmc.derived_values

    @property
    def mcmc_bestparam(self):
        """ best parameter best on the mcmc run. see mcmc_fitvalues for associated errors """
        if not self.has_mcmc():
            raise AttributeError("run mcmc first.")
        return self.mcmc.derived_bestparam
    
        



    # -----------------
    # - derived
    @property
    def covmatrix(self):
        """ coveriance matrix after the fit """
        
        if self.use_minuit:
            if self._migrad_output_[0]["is_valid"]:
                return self.model._read_hess_(np.asarray(self.minuit.matrix()))
            else:
                fakeMatrix = np.zeros((len(self._fitparams),len(self._fitparams)))
                for i,k in enumerate(self.model.freeparameters):
                    fakeMatrix[i,i] = self.minuit.errors[k]**2
                print "*WARNING* Inaccurate covariance Matrix. Only trace defined"
                return self.model._read_hess_(fakeMatrix)
        else:
            if "hess_inv" in self.scipy_output:
                return self.model._read_hess_(self.scipy_output['hess_inv'])
            else:
                fakeHess = np.zeros((len(self.scipy_output["x"]),len(self.scipy_output["x"])))
                for i in range(len(fakeHess)):
                    fakeHess[i,i]=self.scipy_output["jac"][i]
                return self.model._read_hess_(fakeHess)

    # ====================== #
    # = Internal Methods   = #
    # ====================== #
    def _fit_readout_(self):
        """ Gather the output in the readout, you could improve that in you child class"""
        
        for i,name in enumerate(self.model.freeparameters):
            self.fitvalues[name] = self._fitparams[i]
            self.fitvalues[name+".err"] = np.sqrt(self.covmatrix[i,i])
            
        # -- Additional data -- #
        self.fitvalues["chi2"]    = self.get_fval()

    # --------------
    # - Minuit          
    def _fit_minuit_(self,verbose=True):
        """
        """
        self._setup_minuit_()
        print "STARTS MINUIT FIT"
        self._migrad_output_ = self.minuit.migrad()
        
        if self._migrad_output_[0]["is_valid"] is False:
            print "** WARNING ** migrad is not valid"
            self.fitOk = False
        elif verbose:
            self.fitOk = True
            
        self._fitparams = np.asarray([self.minuit.values[k]
                              for k in self.model.freeparameters])
        
        
        
    def _setup_minuit_(self):
        """
        """
        if "_guesses" not in dir(self):
            self.setup_guesses()
        
        # == Minuit Keys == #
        minuit_kwargs = {}
        for param in self.model.freeparameters:
            minuit_kwargs[param]           = self.param_input["%s_guess"%param]
            minuit_kwargs["limit_"+param]  = self.param_input["%s_boundaries"%param]
            minuit_kwargs["fix_"+param]    = self.param_input["%s_fixed"%param]
            
        self.minuit = Minuit(self.model._minuit_chi2_,
                             print_level=1,errordef=1,
                             **minuit_kwargs)

    # ----------------
    # - Scipy              
    def _fit_scipy_(self):
        """ fit using scipy """
        
        from scipy.optimize import minimize
        self._setup_scipy_()
        self.scipy_output = minimize(self.model._scipy_chi2_,
                                    self._paramguess_scipy,bounds=self._parambounds_scipy)
                
        self._fitparams = self.model._read_scipy_parameter_(self.scipy_output["x"])
        self.fitOk         = True
        
    def _setup_scipy_(self):
        """ manages the fixed values and how the parametrisation is made """
        self._paramguess_scipy, self._parambounds_scipy = \
          self.model._parameter2scipyparameter_(self.paramguess,self.parambounds)
    
# ========================================== #
#                                            #
# = Play with Scipy and Minuit Similarly   = #
#                                            #
# ========================================== #

class BaseModel( BaseObject ):
    """ Modeling that are able to manage minuit or scipy inputs"""

    PROPERTIES = ["freeparameters"]
    SIDE_PROPERTIES = ["param_input"]
    DERIVED_PROPERTIES = []

    # =================== #
    # = Initialization  = #
    # =================== #
  
    # =================== #
    # = Fitter Methods  = #
    # =================== #
    def get_set_param_input(self):
        """ return a pseudo param_input dictionnary using the currently
        known parameter information (_guess, _fixed, _boundaries).
        Some might have been set manually when creating the dictionnary.
        If so, they will be in the returned dictionnary.

        Remark: If you set param_input already, this should be a copy.

        Return
        ------
        dictionnary
        """
        infodico = {}
        for name in self.freeparameters:
            for info in ["_guess","_fixed","_boundaries"]:
                if name+info in dir(self):
                    infodico[name+info] = eval("self.%s"%(name+info))
        return infodico

    # ==================== #
    # = Bayesian         = #
    # ==================== #
    # assumes you have a `get_chi2(parameters)` methods
    # and chi2 = -2 * logLikelihood
    def lnprior(self,parameters, verbose=True):
        """ perfectely flat prior, should be change by inheriting classed"""
        if verbose: print "Perfectly flat prior used. Always 0 (set verbose=False to avoid this message)"
        return 0
        
        
    def lnprob(self,parameters):
        """ This is the Bayesian posterior function (in log).
        it returns  lnprior - 0.5*Chi2
        (Assuming Chi2 = -2logLikelihood)
        """
        priors = self.lnprior(parameters)
        if not np.isfinite(priors):
            return -np.inf
        # not sure it works with the _minuit_chi2_/_scipy_chi2_  tricks
        return priors - 0.5*self.get_chi2(parameters)

    # ==================== #
    # = Properties       = #
    # ==================== #
    @property
    def freeparameters(self):
        """ freeparameters for the model.
        You could set FREEPARAMETERS in the global argument of a class to uses this.
        """
        if self._properties["freeparameters"] is None:
            from copy import copy
            self._properties["freeparameters"] = copy(self.FREEPARAMETERS)
        return self._properties["freeparameters"]
    
    @property
    def nparam(self):
        return len(self.freeparameters)
    
    # -----------------------
    # - Parameters Values
    @property
    def param_input(self):
        """ dictionnary containing the input parameter values:
           guess / fixed / bounds

        See also the respective class properties
        """
        if self._side_properties["param_input"] is None:
            self._side_properties["param_input"] = {}
        return self._side_properties["param_input"]
    
    def set_param_input(self,param_input):
        """ Test if you set the parameters inputs """
        for k in param_input.keys():
            if "_guess" not in k and "_fixed" not in k and "_boundaries" not in k:
                raise ValueError("Parameters input must have information like _guess, _fixed, _boundaries only")
        self._side_properties["param_input"] = param_input
        # -- temporary
        for k,v in self._side_properties["param_input"].items():
            self.__dict__[k] = v
            
    @property
    def paramguess(self):
        """ guess put for the fit """
        return [self.param_input["%s_guess"%name]
                for name in self.freeparameters]
    @property
    def parambounds(self):
        """ guess put for the fit """
        return [self.param_input["%s_boundaries"%name]
                for name in self.freeparameters]
        
    @property
    def paramfixed(self):
        """ guess put for the fit """
        return [self.param_input["%s_fixed"%name]
                for name in self.freeparameters]

    # ==================== #
    # = Internal         = #
    # ==================== #
    def _read_hess_(self,hess):
        """
        """
        if len(hess)==len(self.freeparameters):
            return hess
        
        indexFixed = [i for i,name in enumerate(self.freeparameters)
                      if "%s_fixed"%name in dir(self) and eval("self.%s_fixed"%name)]
        for i in indexFixed:
            newhess = np.insert(hess,i,0,axis=0)
            newhess = np.insert(newhess,i,0,axis=1)
            hess = newhess
            
        return hess

    # -------------------
    # - Minuit
    # for the fitter
    def _minuit_chi2_(self,*args,**kwargs):
        """
        """
        raise NotImplementedError(" _minuit_fit_ must be defined in the child function")
    
    # -------------------
    # - Scipy
    # shaped like a minuit 
    def _scipy_chi2_(self,parameter):
        """
        """
        parameter = self._read_scipy_parameter_(parameter)
        return self.get_chi2(parameter)

    def _read_scipy_parameter_(self,parameter):
        """ works opposingly to _parameter2scipyparameter_
        it fills the missing values (the fixed one) with the
        value of the model
        
        parameter: [array]          the scipy-shade parameter

        Return
        ------
        total parameters
        """
        # -- This enable to fasten the code
        if len(parameter) == len(self.freeparameters):
            return parameter
        
        ptotal,ip = [],0
        for name in self.freeparameters:
            if "%s_fixed"%name not in dir(self) or\
               eval("self.%s_fixed"%name) is False:
                ptotal.append(parameter[ip])
                ip +=1
            else:
                ptotal.append(eval("self.%s_guess"%name))
                
        return ptotal
                              
    def _parameter2scipyparameter_(self,guess,bounds,fixed=None):
        """
        = Create what Guess and Bounds scipy must have to account for
          fixed values
        =

        fixed: [array/None]         if you whish to check fixed is correctly
                                    set. Not needed otherwise since this looks
                                    directly to the given `v`_fixed
        """
        scipyGuess,scipyBounds = [],[]
        for name,g,b in zip(self.freeparameters,
                            guess,bounds):
            if "%s_fixed"%name not in dir(self) or\
               eval("self.%s_fixed"%name) is False:
                scipyGuess.append(g)
                scipyBounds.append(b)
                
        return np.asarray(scipyGuess),np.asarray(scipyBounds)