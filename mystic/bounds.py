# This program is in the public domain
# Author: Paul Kienzle
"""
Parameter bounds.

Parameter bounds encompass several features of our optimizers.

First and most trivially they allow for bounded constraints on
parameter values.

Secondly, for parameter values known to follow some distribution,
the bounds encodes a penalty function as the value strays from
its nominal value.  Using a negative log likelihood cost function
on the fit, then this value naturally contributes to the overall
likelihood measure.

Predefined bounds are::

    Unbounded
        range (-inf, inf)
    BoundedBelow
        range (base, inf)
    BoundedAbove
        range (-inf, base)
    Bounded
        range (low, high)
    SoftBounded
        range (low, high) with gaussian probability sigma
    Normal
        range (-inf, inf) with gaussian probability

Using :function:`int_bounds` you can create the appropriate bounded
or unbounded object for the kind of input.

New bounds can be defined following the abstract base class
interface defined in :class:`Bounds`.

For generating bounds given a value, we provide a few helper 
functions::

    pm(x,dx) or pm(x,-dx,+dx)
        return (x-dx,x+dx) limited to 2 significant digits
    pmp(x,p) or pmp(x,-p,+p)
        return (x-p*x/100, x+p*x/100) limited to 2 sig. digits
    pm_raw(x,dx) or raw_pm(x,-dx,+dx) for plus/minus
        return (x-dx,x+dx)
    pmp_raw(x,p) or raw_pmp(x,-p,+p) for plus/minus percent
        return (x-p*x/100, x+p*x/100)
    nice_range(lo,hi)
        return (lo,hi) limited to 2 significant digits
"""
__all__ = ['pm','pmp','pm_raw','pmp_raw', 'nice_range', 'init_bounds',
           'Unbounded', 'Bounded', 'BoundedAbove', 'BoundedBelow',
           'Distribution', 'Normal', 'SoftBounded']

import math
import numpy
from numpy import (isinf, inf, nan, e, pi)
RNG = numpy.random

try:
    from scipy.stats import norm as normal_distribution
except:
    def normal_distribution(*args, **kw):
        raise RuntimeError("scipy.stats unavailable")

def pm(v, *args):
    """
    Return the tuple (~v-dv,~v+dv), where ~expr is a 'nice' number near to
    to the value of expr.  For example::

        >>> r = pm(0.78421, 0.0023145)
        >>> print "%g - %g"%r
        0.7818 - 0.7866

    If called as pm(value, plus, minus), return (~v-minus, ~v+plus).
    """
    return nice_range(pm_raw(v,*args))

def pmp(v, *args):
    """
    Return the tuple (~v-%v,~v+%v), where ~expr is a 'nice' number near to
    the value of expr.  For example::

        >>> r = pmp(0.78421, 10)
        >>> print "%g - %g"%r
        0.7 - 0.87
        >>> r = pmp(0.78421, 0.1)
        >>> print "%g - %g"%r
        0.7834 - 0.785

    If called as pmp(value, plus, minus), return (~v-minus%v, ~v+plus%v).
    """
    return nice_range(pmp_raw(v,*args))

# Generate ranges using x +/- dx or x +/- p%*x
def pm_raw(v, *args):
    """
    Return the tuple [v-dv,v+dv].
    
    If called as called as raw_pm(v,plus,minus), return [v-minus,v+plus)]. 
    """
    if len(args) == 1:
        dv = args[0]
        return v-dv, v+dv
    elif len(args) == 2:
        plus,minus = args
        return v-minus, v+plus
    else:
        raise TypeError("pm(value, delta) or pm(value, plus, minus)")

def pmp_raw(v, *args):
    """
    Return the tuple [v-%v,v+%v]
    
    If called as called as raw_pm(v,plus,minus), return [v-minus,v+plus)]. 
    """
    if len(args) == 1:
        percent = args[0]
        b1,b2 = v*(1-0.01*percent), v*(1+0.01*percent)
    elif len(args) == 2:
        plus,minus = args
        b1,b2 = v*(1-0.01*minus), v*(1+0.01*plus)
    else:
        raise TypeError("pm(value, delta) or pm(value, plus, minus)")

    return (b1,b2) if v>0 else (b2,b1)

def nice_range(range):
    """
    Given a range, return an enclosing range accurate to two digits.
    """
    step = range[1]-range[0]
    if step > 0:
        d = 10**(math.floor(math.log10(step))-1)
        return (math.floor(range[0]/d)*d,math.ceil(range[1]/d)*d)
    else:
        return range

def init_bounds(v):
    """
    Returns a bounds object of the appropriate type given the arguments.

    This is a helper factory to simplify the user interface to parameter
    objects.
    """
    # if it is none, then it is unbounded
    if v == None:
        return Unbounded()

    # if it isn't a tuple, assume it is a bounds type.
    try:
        lo,hi = v
    except TypeError:
        return v

    # if it is a tuple
    if lo == None: lo = inf
    if hi == None: hi = inf
    if isinf(lo) and isinf(hi):
        return Unbounded()
    elif isinf(lo):
        return BoundedAbove(hi)
    elif isinf(hi):
        return BoundedBelow(lo)
    else:
        return Bounded(lo,hi)

class Bounds:
    """
    Bounds abstract base class.

    A range is used for several purposes.  One is that it transforms parameters
    between unbounded and bounded forms, depending on the needs of the optimizer.

    Another is that it generates random values in the range for stochastic
    optimizers, and for initialization.

    A third is that it returns the likelihood of seeing that particular value
    for optimizers which use soft constraints.  Assuming the cost function that
    is being optimized is also a probability, then this is an easy way to
    incorporate information from other sorts of measurements into the model.
    """
    limits = (-inf,inf)
    # TODO: need derivatives wrt bounds transforms
    def get01(self, x):
        """
        Convert the value into [0,1] for optimizers which are bounds constrained.

        This can also be used as a scale bar to show approximately how close to
        the end of the range the value is.
        """
    def put01(self, v):
        """
        Convert [0,1] into the value for optimizers which are bounds constrained.
        """
    def getfull(self, x):
        """
        Convert the value into (-inf,inf) for optimizers which are unconstrained.
        """
    def putfull(self, v):
        """
        Convert (-inf,inf) into the value for optimizers which are unconstrained.
        """
    def random(self, n=1):
        """
        Return a randomly generated valid value.

        The random number generator is assumed to follow the numpy.random
        interface.
        """
    def nllf(self, value):
        """
        Return the negative log likelihood of seeing this value, with
        likelihood scaled so that the maximum probability is one.
        
        For uniform bounds, this either returns zero or inf.  For bounds 
        based on a probability distribution, this returns values between
        zero and inf.  The scaling is necessary so that indefinite and
        semi-definite ranges return a sensible value.  The scaling does
        not affect the likelihood maximization process, though the resulting
        likelihood is not easily interpreted.
        """
    def residual(self, value):
        """
        Return the parameter 'residual' in a way that is consistent with
        residuals in the normal distribution.  The primary purpose is to
        graphically display exceptional values in a way that is familiar
        to the user.  For fitting, the scaled likelihood should be used.
        
        To do this, we will match the cumulative density function value
        with that for N(0,1) and find the corresponding percent point
        function from the N(0,1) distribution.  In this way, for example,
        a value to the right of 2.275% of the distribution would correspond
        to a residual of -2, or 2 standard deviations below the mean.
        
        For uniform distributions, with all values equally probable, we
        use a value of +/-4 for values outside the range, and 0 for values
        inside the range.
        """
    def start_value(self):
        """
        Return a default starting value if none given.
        """
        return self.put01(0.5)
    def __contains__(self, v):
        return self.limits[0] <= v <= self.limits[1]
    def __str__(self):
        limits=[num_format(v) for v in self.limits]
        return "(%s,%s)"%self.limits

#CRUFT: python 2.6 formats indefinite numbers properly on windows?
def num_format(v):
    """
    Number formating which supports inf/nan on windows.
    """
    if numpy.isfinite(v):
        return "%g"%v
    elif numpy.isinf(v):
        return "inf" if v>0 else "-inf"
    else:
        return "NaN"        

class Unbounded(Bounds):
    """
    Unbounded parameter.

    The random initial condition is assumed to be between 0 and 1

    The probability is uniformly 1/inf everywhere, which means the negative 
    log likelihood of P is inf everywhere.  This isn't a particularly useful
    result, since minimizing 
    Likelihood returns 0, so the choice of value doesn't directly affect the fit.

    Convert sign*m*2^e to sign*(e+1023+m), yielding a value in [-2048,2048].
    This can then be converted to a value in [0,1].
    """
    def random(self, n=1):
        return RNG.rand(n)
    def nllf(self, value):
        return 0
    def residual(self, value):
        return 0
    def get01(self, x):
        return _get01_inf(x)
    def put01(self, v):
        return _put01_inf(v)
    def getfull(self, x):
        return x
    def putfull(self, v):
        return v

class BoundedBelow(Bounds):
    """
    Semidefinite range bounded below.

    The random initial condition is assumed to be within 1 of the maximum.

    [base,inf] <-> (-inf,inf) is direct above base+1, -1/(x-base) below
    [base,inf] <-> [0,1] uses logarithmic compression.

    Logarithmic compression works by converting sign*m*2^e+base to
    sign*(e+1023+m), yielding a value in [0,2048]. This can then be
    converted to a value in [0,1].
    """
    def __init__(self, base):
        self.limits = (base,inf)
        self._base = base
    def start_value(self):
        return self._base+1
    def random(self,n=1):
        return self._base + RNG.rand(n)
    def nllf(self, value):
        return 0 if value >= self._base else inf
    def residual(self, value):
        return 0 if value >= self._base else -4
    def get01(self, x):
        (m,e) = math.frexp(x - self._base)
        if m >= 0 and e <= _e_max:
            v = (e + m)
            v = v/(2.*_e_max)
            return v
        else:
            return 0 if m < 0 else 1
    def put01(self, v):
        v = v*2*_e_max
        e = int(v)
        m = v-e
        x = math.ldexp(m,e) + self._base
        return x
    def getfull(self, x):
        v = x - self._base
        return v if v >= 1 else 2-1./v
    def putfull(self, v):
        x = v if v >= 1 else 1./(2-v)
        return x + self._base

class BoundedAbove(Bounds):
    """
    Semidefinite range bounded above.

    [-inf,base] <-> [0,1] uses logarithmic compression
    [-inf,base] <-> (-inf,inf) is direct below base-1, 1/(base-x) above

    Logarithmic compression works by converting sign*m*2^e+base to
    sign*(e+1023+m), yielding a value in [0,2048].  This can then be
    converted to a value in [0,1].
    """
    def __init__(self, base):
        self.limits = (-inf,base)
        self._base = base
    def start_value(self):
        return self._base - 1
    def random(self,n=1):
        return self._base - RNG.rand(n)
    def nllf(self, value):
        return 0 if value <= self._base else inf
    def residual(self, value):
        return 0 if value <= self._base else 4
    def get01(self, x):
        (m,e) = math.frexp(self._base - x)
        if m >= 0 and e <= _e_max:
            v = (e + m)
            v = v/(2.*_e_max)
            return 1-v
        else:
            return 1 if m < 0 else 0
    def put01(self, v):
        v = (1-v)*2*_e_max
        e = int(v)
        m = v-e
        x = -(math.ldexp(m,e) - self._base)
        return x
    def getfull(self, x):
        v = x - self._base
        return v if v <= -1 else -2 - 1./v
    def putfull(self, v):
        x = v if v <= -1 else -1./(v + 2)
        return x + self._base

class Bounded(Bounds):
    """
    Bounded range.

    [lo,hi] <-> [0,1] scale is simple linear
    [lo,hi] <-> (-inf,inf) scale uses exponential expansion
    """
    def __init__(self, lo, hi):
        self.limits = (lo,hi)
    def random(self, n=1):
        lo,hi = self.limits
        return RNG.uniform(lo, hi, size=n)
    def nllf(self, value):
        lo,hi = self.limits
        return 0 if lo<=value<=hi else inf
    def get01(self, x):
        lo,hi = self.limits
        return float(x-lo)/(hi-lo) if hi-lo>0 else 0
    def nllf(self, value):
        lo,hi = self.limits
        if value < lo:
            return -4
        elif value <= hi:
            return 0
        else:
            return 4
    def put01(self, v):
        lo,hi = self.limits
        return (hi-lo)*v + lo
    def getfull(self, x):
        return _put01_inf(self.get01(x))
    def putfull(self, v):
        return self.put01(_get01_inf(v))

class Distribution(Bounds):
    """
    Parameter is pulled from a distribution.
    
    *dist* must implement the distribution interface from scipy.stats.  
    In particular, it should define methods rvs, nnlf, cdf and ppf and 
    attributes args and dist.name.
    """
    N = normal_distribution(0,1)
    def __init__(self, dist):
        self.dist = dist
    def random(self, n=1):
        return self.dist.rvs(n)
    def nllf(self, value):
        return self.dist.nnlf(value)
    def residual(self, value):
        return self.N.ppf(self.dist.cdf(value))
    def get01(self, x):
        return self.dist.cdf(x)
    def put01(self, v):
        return self.dist.ppf(v)
    def getfull(self, x):
        return x
    def putfull(self, v):
        return v
    def __getstate__(self):
        # WARNING: does not preserve and restore seed
        return self.dist.__class__,self.dist.args,self.dist.kwds
    def __setstate__(self, state):
        cls,args,kwds = state
        self.dist = cls(*args, **kwds)
    def __str__(self):
        return "%s(%s)"%(self.dist.dist.name,
                         ",".join(str(s) for s in self.dist.args))

class Normal(Distribution):
    """
    Parameter is pulled from a normal distribution.

    If you have measured a parameter value with some uncertainty (e.g., the
    film thickness is 35+/-5 according to TEM), then you can use this
    measurement to restrict the values given to the search, and to penalize
    choices of this fitting parameter which are different from this value.
    
    *mean* is the expected value of the parameter and *std* is the 1-sigma
    standard deviation.
    """
    
    def __init__(self, mean=0, std=1):
        self.dist = normal_distribution(mean, std)
    def nllf(self, value):
        # P(v) = exp(-0.5*(v-mean)**2/std**2)/sqrt(2*pi*std**2)
        # -log(P(v)) = -(-0.5*(v-mean)**2/std**2 - log( (2*pi*std**2) ** 0.5))
        #            = 0.5*(v-mean)**2/std**2 + log(2*pi)/2 + log(std)
        # Scaling it P(0) = 1 removes the constant term sqrt(2 pi std^2)
        mean,std = self.dist.args
        return 0.5*((value-mean)/std)**2
    def residual(self, value):
        return (value-mean)/std
    def __getstate__(self):
        return self.dist.args # args is mean,std
    def __setstate__(self, state):
        mean,std = state
        self.__init__(mean=mean,std=std)

class SoftBounded(Bounds):
    """
    Parameter is pulled from a stretched normal distribution.

    This is like a rectangular distribution, but with gaussian tails.

    The intent of this distribution is for soft constraints on the values.
    As such, the random generator will return values like the rectangular
    distribution, but the likelihood will return finite values based on
    the distance from the from the bounds rather than returning infinity.

    Note that for bounds constrained optimizers which force the value
    into the range [0,1] for each parameter we don't need to use soft
    constraints, and this acts just like the rectangular distribution,
    but with clipping.
    """
    def __init__(self, lo, hi, width=1):
        self._lo,self._hi,self._width=lo,hi,width
    def random(self, n=1):
        return RNG.uniform(self._lo, self._hi, size=n)
    def nllf(self, value):
        if value < self._lo:
            return (float(self._lo-value)/self._width)**2/2
        elif value > self.hi:
            return (float(value-self._hi)/self._width)**2/2
        else:
            return 0
    def residual(self, value):
        if value < self._lo:
            return -float(self._lo-value)/self._width
        elif value > self.hi:
            return float(value-self._hi)/self._width
        else:
            return 0
    def get01(self, x):
        v = float(x - self._lo)/(self._hi-self._lo)
        return v if 0 <= v <= 1 else (0 if v < 0 else 1)
    def put01(self, v):
        return v*(self._hi-self._lo) + self._lo
    def getfull(self, x):
        return x
    def putfull(self, v):
        return v
    def __str__(self):
        return "stretch_norm(%g,%g,sigma=%g)"%(self._lo,self._hi,self._width)



_e_min = -1023
_e_max = 1024
def _get01_inf(x):
    ## Arctan alternative
    ## Arctan is approximately linear in (-0.5, 0.5), but the
    ## transform is only useful up to (-10**15,10**15).
    # return math.atan(x)/pi + 0.5
    (m,e) = math.frexp(x)
    s = numpy.sign(m)
    v = (e - _e_min + m*s)*s
    v = v/(4.*_e_max) + 0.5
    try:
        v[e<_e_min] = 0
        v[e>_e_max] = 1
    except:
        v = 0 if _e_min > e else (1 if _e_max < e else v)
    return v

def _put01_inf(v):
    ## Arctan alternative
    #return math.tan(pi*(v-0.5))

    v = (v-0.5)*4*_e_max
    s = numpy.sign(v)
    v *= s
    e = int(v)
    m = v-e
    x = math.ldexp(s*m,e+_e_min)
    #print "< x,e,m,s,v",x,e+_e_min,s*m,s,v
    return x
