"""
The Fusion Ring of the Drinfeld Double of a Finite Group
"""
# ****************************************************************************
#  Copyright (C) 2023 Wenqi Li
#                     Daniel Bump <bump at match.stanford.edu>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  https://www.gnu.org/licenses/
# ****************************************************************************
from sage.categories.all import Algebras, AlgebrasWithBasis
from sage.combinat.free_module import CombinatorialFreeModule
from sage.rings.integer_ring import ZZ
from sage.misc.misc import inject_variable
from sage.misc.cachefunc import cached_method
from sage.sets.set import Set
from sage.rings.number_field.number_field import CyclotomicField
from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
from sage.rings.ideal import Ideal
from sage.matrix.constructor import matrix

class FusionDouble(CombinatorialFreeModule):
    r"""
    This constructs the Fusion Ring of the modular tensor category of modules over the Drinfeld
    Double of a finite group. Usage is similar to :class:`FusionRing`::.
    Since many of the methods are similar, we assume the reader is familiar with that
    class.

    INPUT:

    - ``G`` -- a finite group
    - ``prefix`` (optional: defaults to 's') a prefix for the names of simple objects.
    - ``inject_varables`` (optional): set TRUE to create variables for the simple objects.

    REFERENCES:

    - [BaKi2001]_ Chapter 3
    - [Mas1995]_
    - [CHW2015]_
    - [Goff1999]_

    EXAMPLES ::

        sage: G = DihedralGroup(5)
        sage: H = FusionDouble(G, inject_variables=True)
        sage: H.basis()
        Finite family {0: s0, 1: s1, 2: s2, 3: s3, 4: s4, 5: s5, 6: s6, 7: s7, 8: s8, 9: s9, 10: s10, 11: s11, 12: s12, 13: s13, 14: s14, 15: s15}
        sage: for x in H.basis():
        ....:     print ("%s : %s"%(x,x^2))
        ....:
        s0 : s0
        s1 : s0
        s2 : s0 + s1 + s3
        s3 : s0 + s1 + s2
        s4 : s0 + s2 + s3 + s6 + s7 + s8 + s9 + s10 + s11 + s12 + s13 + s14 + s15
        s5 : s0 + s2 + s3 + s6 + s7 + s8 + s9 + s10 + s11 + s12 + s13 + s14 + s15
        s6 : s0 + s1 + s11
        s7 : s0 + s1 + s13
        s8 : s0 + s1 + s15
        s9 : s0 + s1 + s12
        s10 : s0 + s1 + s14
        s11 : s0 + s1 + s6
        s12 : s0 + s1 + s9
        s13 : s0 + s1 + s7
        s14 : s0 + s1 + s10
        s15 : s0 + s1 + s8
        sage: s4*s5
        s1 + s2 + s3 + s6 + s7 + s8 + s9 + s10 + s11 + s12 + s13 + s14 + s15
        sage: s4.ribbon()
        1
        sage: s5.ribbon()
        -1
        sage: s8.ribbon()
        zeta5^3

    If the Fusion Double is multiplicity-free, meaning that the fusion coefficients
    `N_k^{ij}` are bounded by `1`, then the F-matrix may be computed, just as
    for :class:`FusionRing`. There is a caveat here, since even if the fusion
    rules are multiplicity-free, if there are many simple objects, the computation
    may be too large to be practical. At least, this code can compute the F-matrix
    for the Fusion Double of the symmetric group `S_3`, duplicating the result
    of [CHW2015]_ . 

    EXAMPLES ::

        sage: G1 = SymmetricGroup(3)
        sage: H1 = FusionDouble(G1,prefix="u",inject_variables=True)
        sage: F = H1.get_fmatrix()
        Checking multiplicity free-ness

    The above commands create the F-matrix factory. You can compute the F-matrices
    with the command ::

        sage: H1.find_orthogonal_solution()  # not tested (10-15 minutes)

    Individual F-matrices may be computed thus ::

        sage: F.fmatrix(u3,u3,u3,u4) # not tested

    see :class:`FMatrix` for more information.

    Unfortunately beyond `S_3` the number of simple objects is larger.
    Although the :class:`FusionDouble` class and its methods work well
    for groups of moderate size, the FMatrix may not be available.
    For the dihedral group of order 8, there are already 22
    simple objects, and the F-matrix seems out of reach.

    It is an open problem to classify the finite groups whose fusion doubles are
    multiplicity-free. Abelian groups, dihedral groups, dicyclic groups, and all
    groups of order 16 are multiplicity-free.  On the other hand, for groups of order 32,
    some are multiplicity-free and others are not.
    """
    @staticmethod
    def __classcall__(cls, G, prefix="s", inject_variables=False):
        """
        Normalize input to ensure a unique representation.

        TESTS::

            sage: F1 = FusionRing('B3', 2)
            sage: F2 = FusionRing(CartanType('B3'), QQ(2), ZZ)
            sage: F3 = FusionRing(CartanType('B3'), int(2), style="coroots")
            sage: F1 is F2 and F2 is F3
            True

            sage: A23 = FusionRing('A2', 3)
            sage: TestSuite(A23).run()

            sage: B22 = FusionRing('B2', 2)
            sage: TestSuite(B22).run()

            sage: C31 = FusionRing('C3', 1)
            sage: TestSuite(C31).run()

            sage: D41 = FusionRing('D4', 1)
            sage: TestSuite(D41).run()

            sage: G22 = FusionRing('G2', 2)
            sage: TestSuite(G22).run()

            sage: F41 = FusionRing('F4', 1)
            sage: TestSuite(F41).run()

            sage: E61 = FusionRing('E6', 1)
            sage: TestSuite(E61).run()

            sage: E71 = FusionRing('E7', 1)
            sage: TestSuite(E71).run()

            sage: E81 = FusionRing('E8', 1)
            sage: TestSuite(E81).run()
        """
        return super().__classcall__(cls, G, prefix=prefix, inject_variables=inject_variables)

    def __init__(self, G, prefix="s",inject_variables=False):
        self._G = G
        self._prefix = prefix
        self._names = {}
        self._elt = {}
        self._chi = {}
        count = 0
        for g in G.conjugacy_classes_representatives():
            for chi in G.centralizer(g).irreducible_characters():
                self._names[count] = "%s%s"%(prefix, count)
                self._elt[count] = g
                self._chi[count] = chi
                count += 1
        self._rank = count
        self._cyclotomic_order = G.exponent()
        self._basecoer = None
        self._fusion_labels = None
        self._field = None
        cat = AlgebrasWithBasis(ZZ).Subobjects()
        CombinatorialFreeModule.__init__(self, ZZ, [k for k in self._names], category=cat)
        if inject_variables:
            self.inject_variables()

    def _repr_(self):
        return "The Fusion Ring of the Drinfeld Double of %s"%self._G

    def __call__(self, *args):
        if len(args) > 1:
            args = (args,)
        return super(GAlg, self).__call__(*args)

    def _element_constructor(self, k):
        return self.monomial(k)

    def inject_variables(self):
        for i in range(self._rank):
            inject_variable(self._names[i],self.monomial(i))

    def get_order(self):
        r"""
        Return the weights of the basis vectors in a fixed order.
        """
        if self._order is None:
            self.set_order(self.basis().keys().list())
        return self._order

    @cached_method
    def s_ij(self, i, j, unitary=False, base_coercion=True):
        r"""
        Return the element of the S-matrix of this fusion ring
        corresponding to the given elements.
        """
        sum = 0
        G = self._G
        [i, j] = [x.support_of_term() for x in [i,j]]
        [a, chi_1] = [self._elt[i], self._chi[i]]
        [b, chi_2] = [self._elt[j], self._chi[j]]
        for g in G:
            if a*g*b*g.inverse() == g*b*g.inverse()*a:
                sum += chi_1(g*b*g.inverse()) * chi_2(g.inverse()*a*g)
        if unitary:
            coef = 1 / (G.centralizer(a).order() * G.centralizer(b).order())
        else:
            coef = G.order() / (G.centralizer(a).order() * G.centralizer(b).order())
        ret = coef * sum
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)

    def s_ijconj(self, i, j, unitary=False, base_coercion=True):
        """
        Return the conjugate of the element of the S-matrix given by
        ``self.s_ij(elt_i, elt_j, base_coercion=base_coercion)``.

        See :meth:`s_ij`.
        """
        return self.s_ij(i, j, unitary=unitary, base_coercion=base_coercion).conjugate()

    def s_matrix(self, unitary=False, base_coercion=True):
        r"""
        Return the S-matrix of this fusion ring.

        OPTIONAL:

        - ``unitary`` -- (default: ``False``) set to ``True`` to obtain
          the unitary S-matrix

        Without the ``unitary`` parameter, this is the matrix denoted
        `\widetilde{s}` in [BaKi2001]_.

        EXAMPLES::

            sage: D91 = FusionRing("D9", 1)
            sage: D91.s_matrix()
            [          1           1           1           1]
            [          1           1          -1          -1]
            [          1          -1 -zeta136^34  zeta136^34]
            [          1          -1  zeta136^34 -zeta136^34]
            sage: S = D91.s_matrix(unitary=True); S
            [            1/2             1/2             1/2             1/2]
            [            1/2             1/2            -1/2            -1/2]
            [            1/2            -1/2 -1/2*zeta136^34  1/2*zeta136^34]
            [            1/2            -1/2  1/2*zeta136^34 -1/2*zeta136^34]
            sage: S*S.conjugate()
            [1 0 0 0]
            [0 1 0 0]
            [0 0 1 0]
            [0 0 0 1]
        """
        b = self.basis()
        S = matrix([[self.s_ij(b[x], b[y], unitary=unitary, base_coercion=base_coercion)
                     for x in self.get_order()] for y in self.get_order()])
        if unitary:
            return S / self.total_q_order()
        return S

    @cached_method
    def N_ijk(self, i, j, k):
        """
        The symmetric invariant of three simple objects,
        this returns the dimension of

        .. MATH::
           Hom(i \\otimes j\\otimes k, s_0)

        where `s_0` is the unit element (assuming prefix='s').
        Method of computation is through the Verlinde formula.
        """
        sz = self.one()
        return ZZ(sum(self.s_ij(i, r, unitary=True) * self.s_ij(j, r, unitary=True) * self.s_ij(k, r, unitary=True)/self.s_ij(sz, r, unitary=True) for r in self.basis()))

    @cached_method
    def Nk_ij(self, i, j, k):
        r"""
        Returns the fusion coefficient `N^k_{ij}`, computed using the Verlinde formula:

        .. MATH::
            N^k_{ij} = \sum_l \frac{s(i, \ell)\, s(j, \ell)\, \overline{s(k, \ell)}}{s(I, \ell)},

        """
        return self.N_ijk(i, j, self.dual(k))

    def char_Nk_ij(self, i, j, k):
        r"""
        Use character theoretic method to compute the fusion coefficient `N_{ij}^k`.
        Each simple object, for example `i` corresponds to a conjugacy class `\mathcal{C}_i`
        of the underlying group `G`, and an irreducible character `\chi_i` of the
        centralizer `C(g_i)` of a fixed representative `g_i` of `\mathcal{C}_i`. In addition
        to the fixed representative `g_k` of the class `\mathcal{C}_i`
        and `\mathcal{C}_j`, the formula will make use of variable elements `h_i` and
        `h_j` that are subject to the condition `h_ih_j=g_k`.

        .. MATH::

            \frac{|\mathcal{C}_i|}{|G|}\sum_{\substack{h_i\in\mathcal{C}_i\\ h_j\in\mathcal{C}_j\\ h_ih_j=g_k}}|C(h_i)\cap C(h_j)|\,
            \langle\chi_i^{(h_i)}\chi_j^{(h_j)},\chi_k\rangle_{C(h_i)\cap C(h_j)},

        where `\chi_i^{(h_i)}` is the character `\chi_i` of `C(g_i)` conjugated to a
        character of `C(h_i)`, when `h_i` is a conjugate of the fixed representative `g_i`.
        More exactly, there exists `r_i` such that `r_i g_i r_i^{-1}=h_i`, and then
        `\chi_i^{(h_i)}(x)=\chi_i(r_i^{-1}xr_i)`, and this definition does not
        depend on the choice of `r_i`.

        This formula is due to Christopher Goff [Goff1999]_ when the centralizers are normal, 
        and to Wenqi Li in the general case.
        """
        G = self._G
        I = G.conjugacy_class(i.g())
        J = G.conjugacy_class(j.g())
        IJ = Set(I_elem * J_elem for I_elem in I for J_elem in J)
        if k.g() not in IJ:
            return 0

        K = G.conjugacy_class(k.g())
        CI = G.centralizer(i.g())
        CJ = G.centralizer(j.g())
        CK = G.centralizer(k.g())

        c = K.cardinality() / G.order()
        summands = [(I_elem, J_elem) for I_elem in I for J_elem in J if I_elem * J_elem == k.g()]
        res = 0
        for p in summands:
            I_elem, J_elem = p
            for g in G:
                if g.inverse() * i.g() * g == I_elem:
                    i_twist = g
                if g.inverse() * j.g() * g == J_elem:
                    j_twist = g
            A = Set(i_twist.inverse() * zi * i_twist for zi in CI)
            B = Set(j_twist.inverse() * zj * j_twist for zj in CJ)
            inner_summands = A.intersection(B).intersection(Set(CK))
            for x in inner_summands:
                res += i.chi()(i_twist * x * i_twist.inverse()) * j.chi()(j_twist * x * j_twist.inverse()) * k.chi()(x).conjugate()
        return c * res

    @cached_method
    def field(self):
        return CyclotomicField(4 * self._cyclotomic_order)

    def fvars_field(self):
        r"""
        Return a field containing the ``CyclotomicField`` computed by
        :meth:`field` as well as all the F-symbols of the associated
        ``FMatrix`` factory object.

        This method is only available if ``self`` is multiplicity-free.
        """
        if self.is_multiplicity_free():
            return self.get_fmatrix().field()
        raise NotImplementedError("method is only available for multiplicity free fusion rings")

    def root_of_unity(self, r, base_coercion=True):
        r"""
        Return `e^{i\pi r}` as an element of ``self.field()`` if possible.

        INPUT:

        - ``r`` -- a rational number

        EXAMPLES::

            sage: H = FusionDouble(DihedralGroup(6))
            sage: H.field()
            Cyclotomic Field of order 24 and degree 8
            sage: for n in [1..7]:
            ....:     try:
            ....:         print (n,H.root_of_unity(2/n))
            ....:     except ValueError as err:
            ....:         print (n,err)
            ....: 
            1 1
            2 -1
            3 zeta24^4 - 1
            4 zeta24^6
            5 not a root of unity in the field
            6 zeta24^4
            7 not a root of unity in the field
        """
        n = 2 * r * self._cyclotomic_order
        if n not in ZZ:
            raise ValueError("not a root of unity in the field")
        ret = self.field().gen() ** n
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)

    @cached_method
    def r_matrix(self, i, j, k, base_coercion=True):
        r"""
        Return the R-matrix entry corresponding to the subobject ``k``
        in the tensor product of ``i`` with ``j``. This method is only
        correct if the fusion coefficient ``N_{ij}^k\leq 1``. See the
        :class:`FusionRing` method for more information, including
        the reason for this caveat, and the algorithm.
        """
        if self.Nk_ij(i, j, k) == 0:
            return self.field().zero() if (not base_coercion) or (self._basecoer is None) else self.fvars_field().zero()
        if i != j:
            ret = self.root_of_unity((k.twist() - i.twist() - j.twist()) / 2)
        else:
            i0 = self.one()
            B = self.basis()
            ret = sum(y.ribbon()**2 / (i.ribbon() * x.ribbon()**2)
                   * self.s_ij(i0, y) * self.s_ij(i, z) * self.s_ijconj(x, z)
                   * self.s_ijconj(k, x) * self.s_ijconj(y, z) / self.s_ij(i0, z)
                   for x in B for y in B for z in B) / (self.total_q_order()**4)
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)

    def global_q_dimension(self, base_coercion=True):
        r"""
        Return the global quantum dimension, which is the sum of the squares of the
        quantum dimensions of the simple objects.
        For the Drinfeld double, it is the square of the order of the underlying quantum group.

        EXAMPLE ::

            sage: G = SymmetricGroup(4)
            sage: H = FusionDouble(G)
            sage: H.global_q_dimension()
            576
            sage: sum(x.q_dimension()^2 for x in H.basis())
            576
        """
        ret = self._G.order()**2
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)


    def total_q_order(self, base_coercion=True):
        r"""
        Return the positive square root of :meth:`self.global_q_dimension()
        <global_q_dimension>` as an element of :meth:`self.field() <field>`.

        For the Drinfeld double of a finite group `G`, this equals the
        cardinality of `G`.
        """
        ret = self._G.order()
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)

    def D_plus(self, base_coercion=True):
        r"""
        Return `\sum d_i^2\theta_i` where `i` runs through the simple objects,
        `d_i` is the quantum dimension and `\theta_i` is the twist.

        This is denoted `p_+` in [BaKi2001]_ Chapter 3. For the Drinfeld
        double, it equals the order of the group.
        """
        ret = self._G.order()
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)

    def D_minus(self, base_coercion=True):
        r"""
        Return `\sum d_i^2\theta_i^{-1}` where `i` runs through the simple
        objects, `d_i` is the quantum dimension and `\theta_i` is the twist.

        This is denoted `p_-` in [BaKi2001]_ Chapter 3. For the Drinfeld
        double, it equals the order of the group.

        EXAMPLES::

            sage: E83 = FusionRing("E8", 3, conjugate=True)
            sage: [Dp, Dm] = [E83.D_plus(), E83.D_minus()]
            sage: Dp*Dm == E83.global_q_dimension()
            True
            sage: c = E83.virasoro_central_charge(); c
            -248/11
            sage: Dp*Dm == E83.global_q_dimension()
            True
        """
        ret = self._G.order()
        if (not base_coercion) or (self._basecoer is None):
            return ret
        return self._basecoer(ret)

    def is_multiplicity_free(self, verbose=False):
        """
        Returns True if all fusion coefficients are at most 1.
        """
        print ("Checking multiplicity free-ness")
        for i in self.basis():
            for j in self.basis():
                for k in self.basis():
                    if self.N_ijk(i,j,k) > 1:
                        if verbose:
                            print ("N(%s,%s,%s)=%s"%(i,j,k,self.N_ijk(i,j,k)))
                        return False
        return True

    def one(self):
        """
        The unit element of the ring.
        """
        return self.basis()[0]

    @cached_method
    def dual(self,i):
        r"""
        Return the dual object ``i^\ast`` to ``i``.
        """
        sz = self.one()
        for j in self.basis():
            if self.N_ijk(i,j,sz) > 0:
                return j

    def product_on_basis(self, a, b):
        d = {k.support_of_term() : self.N_ijk(self.monomial(a),self.monomial(b),self.dual(k)) for k in self.basis()}
        return self._from_dict(d)

    def _repr_term(self, t):
        return self._names[t]

    def group(self):
        """
        Returns the name of the underlying group.

        EXAMPLE::
            sage: FusionDouble(DiCyclicGroup(4)).group()
            Diyclic group of order 16 as a permutation group
        """
        return self._G

    def IdGroup(self):
        """
        Returns the GAP Small Group identifier. This is a pair ``[n,k]`` where ``n`` is
        the order of the group, and ``k`` is an integer characterizing the
        isomorphism class of the group, available for very many groups.

        EXAMPLE::

            sage: FusionDouble(DiCyclicGroup(4)).IdGroup()
            [ 16, 9 ]

        """
        return self._G._libgap_().IdGroup()

    def get_fmatrix(self, *args, **kwargs):
        """
        Construct an :class:`FMatrix` factory to solve the pentagon and hexagon relations
        and organize the resulting F-symbols.
        """
        if not hasattr(self, 'fmats') or kwargs.get('new', False):
            kwargs.pop('new', None)
            from sage.algebras.fusion_rings.f_matrix import FMatrix
            self.fmats = FMatrix(self, *args, **kwargs)
        return self.fmats

    class Element(CombinatorialFreeModule.Element):
        def is_simple_object(self):
            r"""
            Determine whether ``self`` is a simple object of the fusion ring.
            """
            return self in self.parent().basis()

        def g(self):
           """
           Returns the conjugacy class representative of the underlying
           group corresponding to a simple object.
           """
           return self.parent()._elt[self.support_of_term()]

        def chi(self):
           """
           Returns the character of the centralizer of a conjugacy class
           representative of the underlying group corresponding to a simple object.
           """
           return self.parent()._chi[self.support_of_term()]

        def ribbon(self, base_coercion=True):
            """
            The twist or ribbon of the simple object.

            EXAMPLE::

                sage: H = FusionDouble(CyclicPermutationGroup(3))
                sage: [i.ribbon() for i in H.basis()]
                [1, 1, 1, 1, zeta3, -zeta3 - 1, 1, -zeta3 - 1, zeta3]
            """
            ret = self.chi()(self.g()) / self.chi()(self.parent()._G.one())
            if (not base_coercion) or (self.parent()._basecoer is None):
                return ret
            return self.parent()._basecoer(ret)

        def twist(self, reduced=True):
            r"""
            Return a rational number `h` such that `\theta = e^{i \pi h}`
            is the twist of ``self``. The quantity `e^{i \pi h}` is
            also available using :meth:`ribbon`.

            This method is only available for simple objects.
            """
            if not self.is_simple_object():
                raise ValueError("quantum twist is only available for simple objects of a FusionRing")
            zeta = self.parent().field().gen()
            rib = self.ribbon()
            for k in range(4*self.parent()._cyclotomic_order):
                if zeta**k == rib:
                    return k/(2*self.parent()._cyclotomic_order)

        def dual(self):
            """
            Return the dual of self.

            EXAMPLE::

                sage: G = CyclicPermutationGroup(4)
                sage: H = FusionDouble(G, prefix="b")
                sage: [x for x in H.basis() if x==x.dual()]
                [b0, b1, b8, b9]
            """
            if not self.is_simple_object():
                raise ValueError("dual is only available for simple objects of a FusionRing")
            return self.parent().dual(self)
            return

        @cached_method
        def q_dimension(self, base_coercion=True):
            """
            Return the q-dimension of self.

            EXAMPLE::

                sage: G = AlternatingGroup(4)
                sage: H = FusionDouble(G)
                sage: [x.q_dimension() for x in H.basis()]
                [1, 1, 1, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4]
                sage: sum(x.q_dimension()^2 for x in H.basis()) == G.order()^2
                True
            """
            if not self.is_simple_object():
                raise ValueError("quantum dimension is only available for simple objects of a FusionRing")
            return self.parent().s_ij(self,self.parent().one())


