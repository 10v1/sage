r"""
Euclidean Groups

AUTHORS:

- Volker Braun: initial version
"""

##############################################################################
#       Copyright (C) 2013 Volker Braun <vbraun.name@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#  The full text of the GPL is available at:
#
#                  https://www.gnu.org/licenses/
##############################################################################

from sage.modules.all import FreeModule
from sage.groups.affine_gps.affine_group import AffineGroup


class EuclideanGroup(AffineGroup):
    r"""
    an Euclidean group.

    The Euclidean group `E(A)` (or general affine group) of an affine
    space `A` is the group of all invertible affine transformations from
    the space into itself preserving the Euclidean metric.

    If we let `A_V` be the affine space of a vector space `V`
    (essentially, forgetting what is the origin) then the Euclidean group
    `E(A_V)` is the group generated by the general linear group `SO(V)`
    together with the translations. Recall that the group of translations
    acting on `A_V` is just `V` itself. The general linear and translation
    subgroups do not quite commute, and in fact generate the semidirect
    product

    .. MATH::

        E(A_V) = SO(V) \ltimes V.

    As such, the group elements can be represented by pairs `(A,b)` of a
    matrix and a vector. This pair then represents the transformation

    .. MATH::

        x \mapsto A x + b.

    We can also represent this as a linear transformation in `\dim(V) + 1`
    dimensional space as

    .. MATH::

        \begin{pmatrix}
        A & b \\
        0 & 1
        \end{pmatrix}

    and lifting `x = (x_1, \ldots, x_n)` to `(x_1, \ldots, x_n, 1)`.

    .. SEEALSO::

        - :class:`AffineGroup`

    INPUT:

    Something that defines an affine space. For example

    - An affine space itself:

      * ``A`` -- affine space

    - A vector space:

      * ``V`` -- a vector space

    - Degree and base ring:

      * ``degree`` -- An integer. The degree of the affine group, that
        is, the dimension of the affine space the group is acting on.

      * ``ring`` -- A ring or an integer. The base ring of the affine
        space. If an integer is given, it must be a prime power and
        the corresponding finite field is constructed.

      * ``var`` -- (default: ``'a'``) Keyword argument to specify the finite
        field generator name in the case where ``ring`` is a prime power.

    EXAMPLES::

        sage: E3 = EuclideanGroup(3, QQ); E3
        Euclidean Group of degree 3 over Rational Field
        sage: E3(matrix(QQ,[(6/7, -2/7, 3/7), (-2/7, 3/7, 6/7), (3/7, 6/7, -2/7)]), vector(QQ,[10,11,12]))
              [ 6/7 -2/7  3/7]     [10]
        x |-> [-2/7  3/7  6/7] x + [11]
              [ 3/7  6/7 -2/7]     [12]
        sage: E3([[6/7, -2/7, 3/7], [-2/7, 3/7, 6/7], [3/7, 6/7, -2/7]], [10,11,12])
              [ 6/7 -2/7  3/7]     [10]
        x |-> [-2/7  3/7  6/7] x + [11]
              [ 3/7  6/7 -2/7]     [12]
        sage: E3([6/7, -2/7, 3/7, -2/7, 3/7, 6/7, 3/7, 6/7, -2/7], [10,11,12])
              [ 6/7 -2/7  3/7]     [10]
        x |-> [-2/7  3/7  6/7] x + [11]
              [ 3/7  6/7 -2/7]     [12]

    Instead of specifying the complete matrix/vector information, you can
    also create special group elements::

        sage: E3.linear([6/7, -2/7, 3/7, -2/7, 3/7, 6/7, 3/7, 6/7, -2/7])
              [ 6/7 -2/7  3/7]     [0]
        x |-> [-2/7  3/7  6/7] x + [0]
              [ 3/7  6/7 -2/7]     [0]
        sage: E3.reflection([4,5,6])
              [ 45/77 -40/77 -48/77]     [0]
        x |-> [-40/77  27/77 -60/77] x + [0]
              [-48/77 -60/77   5/77]     [0]
        sage: E3.translation([1,2,3])
              [1 0 0]     [1]
        x |-> [0 1 0] x + [2]
              [0 0 1]     [3]

    Some additional ways to create Euclidean groups::

        sage: A = AffineSpace(2, GF(4,'a'));  A
        Affine Space of dimension 2 over Finite Field in a of size 2^2
        sage: G = EuclideanGroup(A); G
        Euclidean Group of degree 2 over Finite Field in a of size 2^2
        sage: G is EuclideanGroup(2,4) # shorthand
        True

        sage: V = ZZ^3;  V
        Ambient free module of rank 3 over the principal ideal domain Integer Ring
        sage: EuclideanGroup(V)
        Euclidean Group of degree 3 over Integer Ring

        sage: EuclideanGroup(2, QQ)
        Euclidean Group of degree 2 over Rational Field

    TESTS::

        sage: E6 = EuclideanGroup(6, QQ)
        sage: E6 is E6
        True
        sage: V = QQ^6
        sage: E6 is EuclideanGroup(V)
        True
        sage: G = EuclideanGroup(2, GF(5)); G
        Euclidean Group of degree 2 over Finite Field of size 5
        sage: TestSuite(G).run()

    REFERENCES:

    - :wikipedia:`Euclidean_group`
    """
    def _element_constructor_check(self, A, b):
        """
        Verify that ``A``, ``b`` define an affine group element.

        This is called from the group element constructor and can be
        overridden for subgroups of the affine group. It is guaranteed
        that ``A``, ``b`` are in the correct matrix/vector space.

        INPUT:

        - ``A`` -- an element of :meth:`matrix_space`.

        - ``b`` -- an element of :meth:`vector_space`.

        OUTPUT:

        The return value is ignored. You must raise a ``TypeError`` if
        the input does not define a valid group element.

        TESTS::

            sage: E3 = EuclideanGroup(3, QQ)
            sage: A = E3.matrix_space()([6/7,-2/7,3/7,-2/7,3/7,6/7,3/7,6/7,-2/7])
            sage: det(A)
            -1
            sage: b = E3.vector_space().an_element()
            sage: E3._element_constructor_check(A, b)

            sage: A = E3.matrix_space()([1,2,3,4,5,6,7,8,0])
            sage: det(A)
            27
            sage: E3._element_constructor_check(A, b)
            Traceback (most recent call last):
            ...
            TypeError: A must be orthogonal (unitary)
        """
        if not A.is_unitary():
            raise TypeError('A must be orthogonal (unitary)')

    def _latex_(self):
        r"""
        EXAMPLES::

            sage: G = EuclideanGroup(6, GF(5))
            sage: latex(G)
            \mathrm{E}_{6}(\Bold{F}_{5})
        """
        return "\\mathrm{E}_{%s}(%s)"%(self.degree(), self.base_ring()._latex_())

    def _repr_(self):
        """
        String representation of this group.

        EXAMPLES::

            sage: EuclideanGroup(6, GF(5))
            Euclidean Group of degree 6 over Finite Field of size 5
        """
        return "Euclidean Group of degree %s over %s"%(self.degree(), self.base_ring())

    def random_element(self):
        """
        Return a random element of this group.

        EXAMPLES::

            sage: G = EuclideanGroup(4, GF(3))
            sage: G.random_element()  # random
                  [2 1 2 1]     [1]
                  [1 2 2 1]     [0]
            x |-> [2 2 2 2] x + [1]
                  [1 1 2 2]     [2]
            sage: G.random_element() in G
            True

        TESTS::

            sage: G.random_element().A().is_unitary()
            True
        """
        while True:
            v = self.vector_space().random_element()
            try:
                g1 = self.reflection(v)
                break
            except ValueError: # v has norm zero
                pass
        g2 = self.translation(self.vector_space().random_element())
        return g1 * g2

