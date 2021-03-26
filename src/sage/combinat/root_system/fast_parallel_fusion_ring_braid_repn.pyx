"""
Fast FusionRing methods for computing braid group representations
"""
# ****************************************************************************
#  Copyright (C) 2021 Guillermo Aboumrad <gh_willieab>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  https://www.gnu.org/licenses/
# ****************************************************************************

cimport cython
import ctypes
from itertools import product
import sage
from sage.combinat.root_system.poly_tup_engine cimport _flatten_coeffs, _unflatten_coeffs, poly_to_tup
from sage.combinat.root_system.fast_parallel_fmats_methods cimport _fmat
from sage.misc.cachefunc import cached_function
from sage.rings.qqbar import QQbar

#Define a global temporary worker results repository
worker_results = list()

##############################
### Parallel code executor ###
##############################

def executor(params):
    """
    Execute a function defined in this module
    (sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn)
    in a worker process, and supply the factory parameter by constructing a
    reference to the FMatrix object in the worker's memory adress space
    from its id.

    NOTES:

    When the parent process is forked, each worker gets a copy of
    every  global variable. The virtual memory address of object X in the parent
    process equals the VIRTUAL memory address of the copy of object X in each
    worker, so we may construct references to forked copies of X

    TESTS:

        sage: from sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn import executor
        sage: FR = FusionRing("A1",4)
        sage: FR.fusion_labels(['idd','one','two','three','four'],inject_variables=True)
        sage: params = (('sig_2k',id(FR)),(0,1,(1,one,one,5)))
        sage: executor(params)
        sage: from sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn import collect_results
        sage: len(collect_results(0)) == 13
        True
        sage: from sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn import executor, collect_results
        sage: FR = FusionRing("B2",2)
        sage: FR.fusion_labels(['I0','Y1','X','Z','Xp','Y2'],inject_variables=True)
        sage: params = (('odd_one_out',id(FR)),(0,1,(X,Xp,5)))
        sage: executor(params)
        sage: len(collect_results(0)) == 54
        True
    """
    (fn_name, fr_id), args = params
    #Construct a reference to global FMatrix object in this worker's memory
    fusion_ring_obj = ctypes.cast(fr_id, ctypes.py_object).value
    mod = sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn
    #Bind module method to FMatrix object in worker process, and call the method
    getattr(mod,fn_name)(fusion_ring_obj,args)

###############
### Mappers ###
###############

cpdef mid_sig_ij(fusion_ring,row,col,a,b):
    """
    Compute the (xi,yi), (xj,yj) entry of generator braiding the middle two strands
    in the tree b -> xi # yi -> (a # a) # (a # a), which results in a sum over j
    of trees b -> xj # yj -> (a # a) # (a # a)

    .. WARNING::

        This method assumes F-matrices are orthogonal

    EXAMPLES::

        sage: from sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn import mid_sig_ij
        sage: FR = FusionRing("A1",4)
        sage: FR.fusion_labels(['idd','one','two','three','four'],inject_variables=True)
        sage: one.weight()
        (1/2, -1/2)
        sage: FR.get_computational_basis(one,two,4)
        [(two, two), (two, idd), (idd, two)]
        sage: mid_sig_ij(FR, (two, two), (two, idd), one, two)
        (zeta48^10 - zeta48^2)*fx0*fx1*fx8 + (zeta48^2)*fx2*fx3*fx8
    """
    #Pre-compute common parameters for efficiency
    _fvars = fusion_ring.fmats._fvars
    _Nk_ij = fusion_ring.Nk_ij
    one = fusion_ring.one()

    xi, yi = row
    xj, yj = col
    entry = 0
    for c in fusion_ring.basis():
        for d in fusion_ring.basis():
            ##Warning: We assume F-matrices are orthogonal!!! (using transpose for inverse)
            f1 = _fmat(_fvars,_Nk_ij,one,a,a,yi,b,xi,c)
            f2 = _fmat(_fvars,_Nk_ij,one,a,a,a,c,d,yi)
            f3 = _fmat(_fvars,_Nk_ij,one,a,a,a,c,d,yj)
            f4 = _fmat(_fvars,_Nk_ij,one,a,a,yj,b,xj,c)
            r = fusion_ring.r_matrix(a,a,d)
            entry += f1 * f2 * r * f3 * f4
    return entry

cpdef odd_one_out_ij(fusion_ring,xi,xj,a,b):
    r"""
    Compute the `xi`, `xj` entry of the braid generator on the two right-most
    strands, corresponding to the tree b -> (xi # a) -> (a # a) # a, which
    results in a sum over j of trees b -> xj -> (a # a) # (a # a)

    .. WARNING::

        This method assumes F-matrices are orthogonal

    EXAMPLES::

        sage: from sage.combinat.root_system.fast_parallel_fusion_ring_braid_repn import odd_one_out_ij
        sage: FR = FusionRing("B2",2)
        sage: FR.fusion_labels(['I0','Y1','X','Z','Xp','Y2'],inject_variables=True)
        sage: X.weight()
        (1/2, 1/2)
        sage: FR.get_computational_basis(X,X,3)
        [(Y2,), (Y1,), (I0,)]
        sage: odd_one_out_ij(FR,Y2,Y1,X,X)
        (zeta40^10)*fx205*fx208 + (zeta40^14 - zeta40^10 + zeta40^6 - zeta40^2)*fx206*fx209 + (zeta40^2)*fx207*fx210
    """
    #Pre-compute common parameters for efficiency
    _fvars = fusion_ring.fmats._fvars
    _Nk_ij = fusion_ring.Nk_ij
    one = fusion_ring.one()

    entry = 0
    for c in fusion_ring.basis():
        ##Warning: We assume F-matrices are orthogonal!!! (using transpose for inverse)
        f1 = _fmat(_fvars,_Nk_ij,one,a,a,a,b,xi,c)
        f2 = _fmat(_fvars,_Nk_ij,one,a,a,a,b,xj,c)
        r = fusion_ring.r_matrix(a,a,c)
        entry += f1 * r * f2
    return entry

#Cache methods
mid_sig_ij = cached_function(mid_sig_ij, name='mid_sig_ij')
odd_one_out_ij = cached_function(odd_one_out_ij, name='odd_one_out_ij')

#@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cpdef sig_2k(fusion_ring, tuple args):
    """
    Compute entries of the 2k-th braid generator
    """
    #Pre-compute common parameters for efficiency
    _fvars = fusion_ring.fmats._fvars
    _Nk_ij = fusion_ring.Nk_ij
    one = fusion_ring.one()

    child_id, n_proc, fn_args = args
    k, a, b, n_strands = fn_args
    cdef int ctr = -1
    global worker_results
    #Get computational basis
    cdef list comp_basis = fusion_ring.get_computational_basis(a,b,n_strands)
    cdef dict basis_dict = { elt : i for i, elt in enumerate(comp_basis) }
    cdef int dim = len(comp_basis)
    cdef set coords = set()
    cdef int i
    #Avoid pickling cyclotomic field element objects
    must_flatten_coeff = fusion_ring.fvars_field() != QQbar
    for i in range(dim):
        for f,e,q in product(fusion_ring.basis(),repeat=3):
            #Distribute work amongst processes
            ctr += 1
            if ctr % n_proc != child_id:
                continue

            #Compute appropriate possible nonzero row index
            nnz_pos = list(comp_basis[i])
            nnz_pos[k-1:k+1] = f,e
            #Handle the special case k = 1
            if k > 1:
                nnz_pos[n_strands//2+k-2] = q
            nnz_pos = tuple(nnz_pos)

            #Skip repeated entries when k = 1
            if nnz_pos in comp_basis and (basis_dict[nnz_pos],i) not in coords:
                m, l = comp_basis[i][:n_strands//2], comp_basis[i][n_strands//2:]
                #A few special cases
                top_left = m[0]
                if k >= 3:
                    top_left = l[k-3]
                root = b
                if k - 1 < len(l):
                    root = l[k-1]

                #Handle the special case k = 1
                if k == 1:
                    entry = mid_sig_ij(fusion_ring,m[:2],(f,e),a,root)

                    #Avoid pickling cyclotomic field element objects
                    if must_flatten_coeff:
                        entry = _flatten_entry(fusion_ring, entry)

                    worker_results.append(((basis_dict[nnz_pos],i), entry))
                    coords.add((basis_dict[nnz_pos],i))
                    continue

                entry = 0
                for p in fusion_ring.basis():
                    f1 = _fmat(_fvars,_Nk_ij,one,top_left,m[k-1],m[k],root,l[k-2],p)
                    f2 = _fmat(_fvars,_Nk_ij,one,top_left,f,e,root,q,p)
                    entry += f1 * mid_sig_ij(fusion_ring,(m[k-1],m[k]),(f,e),a,p) * f2

                #Avoid pickling cyclotomic field element objects
                if must_flatten_coeff:
                    #The entry is either a polynomial or a base field element
                    if entry.parent() == fusion_ring.fmats._poly_ring:
                        entry = _flatten_coeffs(poly_to_tup(entry))
                    else:
                        entry = entry.list()

                worker_results.append(((basis_dict[nnz_pos],i), entry))

#@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cpdef odd_one_out(fusion_ring, tuple args):
    """
    Compute entries of the rightmost braid generator, in case we have an odd number
    of strands
    """
    #Pre-compute common parameters for efficiency
    _fvars = fusion_ring.fmats._fvars
    _Nk_ij = fusion_ring.Nk_ij
    one = fusion_ring.one()

    global worker_results
    child_id, n_proc, fn_args = args
    a, b, n_strands = fn_args
    cdef ctr = -1
    #Get computational basis
    comp_basis = fusion_ring.get_computational_basis(a,b,n_strands)
    basis_dict = { elt : i for i, elt in enumerate(comp_basis) }
    dim = len(comp_basis)

    #Avoid pickling cyclotomic field element objects
    must_flatten_coeff = fusion_ring.fvars_field() != QQbar
    for i in range(dim):
        for f, q in product(fusion_ring.basis(),repeat=2):
            #Distribute work amongst processes
            ctr += 1
            if ctr % n_proc != child_id:
                continue

            #Compute appropriate possible nonzero row index
            nnz_pos = list(comp_basis[i])
            nnz_pos[n_strands//2-1] = f
            #Handle small special case
            if n_strands > 3:
                nnz_pos[-1] = q
            nnz_pos = tuple(nnz_pos)

            if nnz_pos in comp_basis:
                m, l = comp_basis[i][:n_strands//2], comp_basis[i][n_strands//2:]

                #Handle a couple of small special cases
                if n_strands == 3:
                    entry = odd_one_out_ij(fusion_ring,m[-1],f,a,b)

                    #Avoid pickling cyclotomic field element objects
                    if must_flatten_coeff:
                        #The entry is either a polynomial or a base field element
                        if entry.parent() == fusion_ring.fmats._poly_ring:
                            entry = _flatten_coeffs(poly_to_tup(entry))
                        else:
                            entry = entry.list()

                    worker_results.append(((basis_dict[nnz_pos],i), entry))
                    continue
                top_left = m[0]
                if n_strands > 5:
                    top_left = l[-2]
                root = b

                #Compute relevant entry
                entry = 0
                for p in fusion_ring.basis():
                    f1 = _fmat(_fvars,_Nk_ij,one,top_left,m[-1],a,root,l[-1],p)
                    f2 = _fmat(_fvars,_Nk_ij,one,top_left,f,a,root,q,p)
                    entry += f1 * odd_one_out_ij(fusion_ring,m[-1],f,a,p) * f2

                #Avoid pickling cyclotomic field element objects
                if must_flatten_coeff:
                    entry = _flatten_entry(fusion_ring, entry)

                worker_results.append(((basis_dict[nnz_pos],i), entry))

################
### Reducers ###
################

def collect_results(proc):
    """
    Helper function for returning processed results back to parent process.
    Trivial reducer: simply collects objects with the same key in the worker
    """
    #Discard the zero polynomial
    global worker_results
    reduced = worker_results #set(worker_results)-set([tuple()])
    worker_results = list()
    return reduced

######################################
### Pickling circumvention helpers ###
######################################

cdef _flatten_entry(fusion_ring, entry):
    #The entry is either a polynomial or a base field element
    if entry.parent() == fusion_ring.fmats._poly_ring:
        entry = _flatten_coeffs(poly_to_tup(entry))
    else:
        entry = entry.list()
    return entry

cpdef _unflatten_entries(factory, list entries):
    F = factory.fvars_field()
    fm = factory.fmats
    must_unflatten = F != QQbar
    if must_unflatten:
        for i, (coord, entry) in enumerate(entries):
            #In this case entry represents a polynomial
            if type(entry) == type(tuple()):
                entry = fm.tup_to_fpoly(_unflatten_coeffs(F,entry))
            #Otherwise entry belongs to base field
            else:
                entry = F(entry)
            entries[i] = (coord, entry)
