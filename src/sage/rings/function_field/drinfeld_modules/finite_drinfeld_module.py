r"""
Finite Drinfeld modules

This module provides the class
:class:`sage.rings.function_fields.drinfeld_module.finite_drinfeld_module.FiniteDrinfeldModule`,
which inherits
:class:`sage.rings.function_fields.drinfeld_module.drinfeld_module.DrinfeldModule`.

AUTHORS:

- Antoine Leudière (2022-04)
"""

#*****************************************************************************
#       Copyright (C) 2022 Antoine Leudière <antoine.leudiere@inria.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
from sage.rings.function_field.drinfeld_modules.drinfeld_module import DrinfeldModule

class FiniteDrinfeldModule(DrinfeldModule):
    r"""
    This class represnets a finite Drinfeld module.

    A *finite Drinfeld module* is a Drinfeld module whose base ring is
    finite. For general definitions and help on Drinfeld modules, see
    class
    :class:`sage.rings.function_fields.drinfeld_module.drinfeld_module.DrinfeldModule`.
    In this specific documentation, we only present the specifics of
    ``FiniteDrinfeldModle``.

    The user does not ever need to directly call
    ``FiniteDrinfeldModule``, as it is the (meta)class
    ``DrinfeldModule`` that is reponsible for instanciating
    ``DrinfeldModule`` or ``FiniteDrinfeldModule`` depending on its
    input::

        sage: Fq = GF(343)
        sage: FqX.<X> = Fq[]
        sage: K.<z6> = Fq.extension(2)
        sage: phi = DrinfeldModule(FqX, [z6, 0, 5])
        sage: isinstance(phi, DrinfeldModule)
        True
        sage: from sage.rings.function_field.drinfeld_modules.finite_drinfeld_module import FiniteDrinfeldModule
        sage: isinstance(phi, FiniteDrinfeldModule)
        True

    But, the user should never use ``FiniteDrinfeldModule`` to test if a
    Drinfeld module is finite, but rather the ``is_finite`` method::

        sage: phi.is_finite()
        True

    .. RUBRIC:: Complex multiplication of rank two finite Drinfeld modules

    We can handle some aspects of the theory of complex multiplication
    of finite Drinfeld modules. Apart from the method
    ``frobenius_endomorphism``, we only handle rank two Drinfeld
    modules.

    First of all, it is easy to create the Frobenius endomorphism::

        sage: frobenius_endomorphism = phi.frobenius_endomorphism()
        sage: frobenius_endomorphism
        Drinfeld Module morphism:
          From: Drinfeld module defined by X |--> 5*t^2 + z6 over Finite Field in z6 of size 7^6
          To:   Drinfeld module defined by X |--> 5*t^2 + z6 over Finite Field in z6 of size 7^6
          Defn: t^2

    Its characteristic polynomial can be computed::

        sage: chi = phi.frobenius_charpoly()
        sage: chi
        T^2 + (X + 2*z3^2 + 2*z3 + 1)*T + 2*X^2 + (z3^2 + z3 + 4)*X + 2*z3
        sage: frob_pol = frobenius_endomorphism.ore_polynomial()
        sage: chi(frob_pol, phi(X))
        0

    This makes it possible to compute the Frobenius trace and norm::

        sage: phi.frobenius_trace()
        6*X + 5*z3^2 + 5*z3 + 6
        sage: phi.frobenius_trace() == -chi[1]
        True
        sage: phi.frobenius_norm()
        2*X^2 + (z3^2 + z3 + 4)*X + 2*z3

    And to decide if a Drinfeld module is ordinary or supersingular::

        sage: phi.is_ordinary()
        True
        sage: phi.is_supersingular()
        False
    """

    def __init__(self, gen, category):

        # NOTE: There used to be no __init__ here (which was fine). I
        # added one to ensure that FiniteDrinfeldModule would always
        # have _frobenius_norm and _frobenius_trace attributes.

        super().__init__(gen, category)
        self._frobenius_norm = None
        self._frobenius_trace = None

    def frobenius_endomorphism(self):
        r"""
        Return the Frobenius endomorphism, as an instance of
        ``DrinfeldModuleMorphism``, of the Drinfeld module, if the rank
        is two; raise a NotImplementedError otherwise..

        Let `q` be the order of the base field of the function ring. The
        *Frobenius endomorphism* is defined as the endomorphism whose
        defining Ore polynomial is `t^q`.

        OUTPUT:

        - a Drinfeld module morphism

        EXAMPLES:

            sage: Fq = GF(343)
            sage: FqX.<X> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(FqX, [1, 0, z6])
            sage: phi.frobenius_endomorphism()
            Drinfeld Module morphism:
              From: Drinfeld module defined by X |--> z6*t^2 + 1 over Finite Field in z6 of size 7^6
              To:   Drinfeld module defined by X |--> z6*t^2 + 1 over Finite Field in z6 of size 7^6
              Defn: t^2
            sage: from sage.rings.function_field.drinfeld_modules.morphism import DrinfeldModuleMorphism
            sage: isinstance(phi.frobenius_endomorphism(), DrinfeldModuleMorphism)
            True
        """
        t = self.ore_variable()
        L = self._base_ring
        Fq = self._function_ring.base_ring()
        deg = L.over(Fq).degree(Fq)
        return self._Hom_(self, category=self.category())(t**deg)

    def frobenius_charpoly(self, var='T'):
        r"""
        Return the characteristic polynomial of the Frobenius
        endomorphism, if the rank is two; raise a NotImplementedError
        otherwise.

        Let `\Fq` be the base field of the function ring. The
        *characteristic polynomial `\chi` of the Frobenius endomorphism* is
        defined in [Gek1991]_. An important feature of this polynomial
        is that it is a monic bivariate polynomial in `T` with
        coefficients in `\Fq[X]`. Write `\chi = T^2 - A(X)T + B(X)`, let
        `t^n` be the Ore polynomial that defines the Frobenius
        endomorphism of `\phi`; by definition, `n` is the degree of the
        base ring over `\Fq`. We have `\chi(t^n)(\phi(X)) = t^{2n} -
        \phi_A t^n + \phi_B = 0`, with `\deg(A) \leq \frac{n}{2}` and
        `\deg(B) = n`.

        Note that the *Frobenius trace* is defined as `A(X)` and the
        *Frobenius norm` is defined as `B(X)`.

        INPUT:

        - ``var`` -- (optional) the name of the second variable

        OUTPUT:

        - a polynomial in `\Fq[X][T]`

        EXAMPLES:

            sage: Fq = GF(343)
            sage: FqX.<X> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(FqX, [1, 0, z6])
            sage: chi = phi.frobenius_charpoly()
            sage: chi
            T^2 + ((3*z3^2 + z3 + 4)*X + 4*z3^2 + 6*z3 + 3)*T + (5*z3^2 + 2*z3)*X^2 + (4*z3^2 + 3*z3)*X + 5*z3^2 + 2*z3

            sage: frob_pol = phi.frobenius_endomorphism().ore_polynomial()
            sage: chi(frob_pol, phi(X))
            0

            sage: A = phi.frobenius_trace()
            sage: A
            (4*z3^2 + 6*z3 + 3)*X + 3*z3^2 + z3 + 4
            sage: B = phi.frobenius_norm()
            sage: B
            (5*z3^2 + 2*z3)*X^2 + (4*z3^2 + 3*z3)*X + 5*z3^2 + 2*z3

            sage: n = 2  # Degree of the base ring over `\Fq`
            sage: A.degree() <= n/2
            True
            sage: B.degree() == n
            True

        ALGORITHM:

            We compute the Frobenius norm, and with it the Frobenius
            trace. This gives the Frobenius characteristic polynomial.
            See [SM2019]_, Section 4.

            See docstrings of methods
            :meth:`sage.rings.function_fields.drinfeld_module.finite_drinfeld_module.FiniteDrinfeldModule.frobenius_norm`
            and
            :meth:`sage.rings.function_fields.drinfeld_module.finite_drinfeld_module.FiniteDrinfeldModule.frobenius_trace`
            for furthere details on the computation of the norm and of
            the trace.
        """
        self._check_rank_two()
        A = self._function_ring  # Fq[X]
        S = PolynomialRing(A, name=var)  # Fq[X][T]
        # Does not work when Fq is not a prime field...
        # chi = self._gen.reduced_charpoly()
        # return -chi(A.gen(), S.gen())
        return S([self.frobenius_norm(), -self.frobenius_trace(), 1])

    def frobenius_norm(self):
        r"""
        Return Frobenius norm of the Drinfeld module, if the rank is
        two; raise a NotImplementedError otherwise.

        Write `\chi = T^2 - A(X)T + B(X) \in \Fq[X][T]` to be the
        characteristic polynomial of the Frobenius endomorphism. The
        *Frobenius norm* is defined as the polynomial `B(X) \in \Fq[X]`.

        Let `n` be the degree of the base ring over `\Fq`. Then the
        Frobenius norm has degree `n`.

        OUTPUT:

        - a polynomial in `\Fq[X]`

        EXAMPLES:

            sage: Fq = GF(343)
            sage: FqX.<X> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(FqX, [1, 0, z6])
            sage: B = phi.frobenius_norm()
            sage: B
            (5*z3^2 + 2*z3)*X^2 + (4*z3^2 + 3*z3)*X + 5*z3^2 + 2*z3

            sage: n = 2  # Degree of the base ring over `\Fq`
            sage: B.degree() == n
            True

            sage: B == phi.frobenius_charpoly()[0]
            True

        ALGORITHM:

            The Frobenius norm is computed using the formula, by
            Gekeler, given in [SM2019]_, Section 4, Proposition 3.
        """
        self._check_rank_two()
        # Notations from Schost-Musleh:
        if self._frobenius_norm is None:
            n = self._base_ring.over(self._Fq).degree_over(self._Fq)
            d = self.characteristic().degree()
            m = n // d
            delta = self._gen[2]
            norm = self._base_ring.over(self._Fq)(delta).norm()
            self._frobenius_norm = ((-1)**n) * (self.characteristic()**m) / norm
        return self._frobenius_norm

    def frobenius_trace(self):
        r"""
        Return Frobenius norm of the Drinfeld module, if the rank is
        two; raise a NotImplementedError otherwise.

        Write `\chi = T^2 - A(X)T + B(X) \in \Fq[X][T]` to be the
        characteristic polynomial of the Frobenius endomorphism. The
        *Frobenius norm* is defined as the polynomial `B(X) \in \Fq[X]`.

        Let `n` be the degree of the base ring over `\Fq`. Then the
        Frobenius trace has degree `\leq \frac{n}{2}`.

        OUTPUT:

        - a polynomial in `\Fq[X]`

        ALGORITHM:

            Let `A(X)` denote the Frobenius trace and `B(X)` denote the
            Frobenius norm. We begin by computing `B(X)`, see docstring
            of method
            :meth:`sage.rings.function_fields.drinfeld_module.finite_drinfeld_module.FiniteDrinfeldModule.frobenius_norm`
            for details. The characteristic polynomial of the Frobenius
            yields `t^{2n} - \phi_A t^n + \phi_B = 0`, where `t^n` is
            the Frobenius endomorphism. As `\phi_B` is now known, we can
            compute `\phi_A = (t^{2n} + \phi_B) / t^n`. We get `A(X)` by
            inverting this quantity, using the method
            :meth:`sage.rings.function_fields.drinfeld_module.drinfeld_module.DrinfeldModule.invert`,
            see its docstring for details.

        EXAMPLES:

            sage: Fq = GF(343)
            sage: FqX.<X> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(FqX, [1, 0, z6])
            sage: A = phi.frobenius_trace()
            sage: A
            (4*z3^2 + 6*z3 + 3)*X + 3*z3^2 + z3 + 4

            sage: n = 2  # Degree of the base ring over `\Fq`
            sage: A.degree() <= n/2
            True

            sage: A == -phi.frobenius_charpoly()[1]
            True
        """
        self._check_rank_two()
        # Notations from Schost-Musleh:
        if self._frobenius_trace is None:
            n = self._base_ring.over(self._Fq).degree_over(self._Fq)
            B = self.frobenius_norm()
            t = self.ore_polring().gen()
            self._frobenius_trace = self.invert(t**n + (self(B) // t**n))
        return self._frobenius_trace

    def is_ordinary(self):
        r"""
        Return True if the Drinfeld module is ordinary, return False
        otherwise; raise a NotImplementedError if the rank is not two.

        A rank two finite Drinfeld module is *ordinary* if and only if
        the `\Fq[X]-characteristic of the base ring does not devide the
        Frobenius trace. A *supersingular* rank two finite Drinfeld
        module is a Drinfeld module that is not ordinary.

        OUTPUT:

        - a boolean

        EXAMPLES:

            sage: Fq = GF(343)
            sage: FqX.<X> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(FqX, [1, 0, z6])
            sage: phi.is_ordinary()
            False
            sage: phi_p = phi(phi.characteristic())
            sage: phi_p  # Purely inseparable
            z6*t^2

        ALGORITHM:

            Compute the Frobenius trace and test if the `\Fq[X]`
            characteristic divides it.

            We could also test if the image of the
            `\Fq[X]`-characteristic under the Drinfeld module is purely
            inseparable; see [Gek1991]_, Proposition 4.1.
        """
        self._check_rank_two()
        return not self.is_supersingular()

    def is_supersingular(self):
        r"""
        Return True if the Drinfeld module is supersingular, return False
        otherwise; raise a NotImplementedError if the rank is not two.

        A rank two finite Drinfeld module is *supersingular* if and only
        if the `\Fq[X]-characteristic of the base ring devides the
        Frobenius trace. An *ordinary* rank two finite Drinfeld module
        is a Drinfeld module that is not supersingular.

        OUTPUT:

        - a boolean

        EXAMPLES:

            sage: Fq = GF(343)
            sage: FqX.<X> = Fq[]
            sage: K.<z6> = Fq.extension(2)
            sage: phi = DrinfeldModule(FqX, [1, 0, z6])
            sage: phi.is_supersingular()
            True
            sage: phi_p = phi(phi.characteristic())
            sage: phi_p  # Purely inseparable
            z6*t^2

        ALGORITHM:

            Compute the Frobenius trace and test if the `\Fq[X]`
            characteristic divides it.

            We could also test if the image of the
            `\Fq[X]`-characteristic under the Drinfeld module is purely
            inseparable; see [Gek1991]_, Proposition 4.1.
        """
        self._check_rank_two()
        return self.characteristic().divides(self.frobenius_trace())
