r"""
Set of morphisms between two Drinfeld modules

This module provides the class
:class:`sage.rings.function_field.drinfeld_module.homset.DrinfeldModuleHomset`.

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

from sage.categories.drinfeld_modules import DrinfeldModules
from sage.categories.homset import Homset, Hom
from sage.misc.latex import latex
from sage.rings.function_field.drinfeld_modules.morphism import DrinfeldModuleMorphism
from sage.structure.parent import Parent

class DrinfeldModuleHomset(Homset):
    r"""
    This class represents the set of morphisms between two Drinfeld
    modules.

    INPUT:

    - ``X`` -- the domain
    - ``Y`` -- the codomain

    EXAMPLES:

        sage: Fq = GF(27)
        sage: FqX.<X> = Fq[]
        sage: K.<z6> = Fq.extension(2)
        sage: phi = DrinfeldModule(FqX, [z6, z6, 2])
        sage: psi = DrinfeldModule(FqX, [z6, 2*z6^5 + 2*z6^4 + 2*z6 + 1, 2])
        sage: hom = Hom(phi, psi)
        sage: hom
        Set of Drinfeld module morphisms:
          From: Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          To:   Drinfeld module defined by X |--> 2*t^2 + (2*z6^5 + 2*z6^4 + 2*z6 + 1)*t + z6 over Finite Field in z6 of size 3^6

        sage: from sage.rings.function_field.drinfeld_modules.homset import DrinfeldModuleHomset
        sage: isinstance(hom, DrinfeldModuleHomset)
        True

    There is a simpler syntax for endomorphisms sets::

        sage: end = End(phi)
        sage: end
        Set of Drinfeld module morphisms:
          From: Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          To:   Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
        sage: end is Hom(phi, phi)
        True


    One can create morphism objects by calling the homset::

        sage: t = phi.ore_variable()
        sage: identity_morphism = end(1)
        sage: identity_morphism
        Drinfeld Module morphism:
          From: Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          To:   Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          Defn: 1

        sage: frobenius_endomorphism = end(t^6)
        sage: frobenius_endomorphism
        Drinfeld Module morphism:
          From: Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          To:   Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          Defn: t^6

        sage: isogeny = hom(t + 1)
        sage: isogeny
        Drinfeld Module morphism:
          From: Drinfeld module defined by X |--> 2*t^2 + z6*t + z6 over Finite Field in z6 of size 3^6
          To:   Drinfeld module defined by X |--> 2*t^2 + (2*z6^5 + 2*z6^4 + 2*z6 + 1)*t + z6 over Finite Field in z6 of size 3^6
          Defn: t + 1

    And one can test if an Ore polynomial defines a morphism using the
    ``in`` syntax::

        sage: 1 in hom
        False
        sage: t^6 in hom
        False
        sage: t + 1 in hom
        True
        sage: 1 in end
        True
        sage: t^6 in end
        True
        sage: t + 1 in end
        False

    This also works if the candidate is a morphism object::

        sage: isogeny in hom
        True
        sage: end(0) in end
        True
        sage: identity_morphism in hom
        False
        sage: frobenius_endomorphism in hom
        False
    """
    
    Element = DrinfeldModuleMorphism
    __contains__ = Parent.__contains__

    def __init__(self, X, Y, category=None, check=True):
        if category is None:
            category = X.category()
        if check:
            if X.category() != Y.category() \
                    or not isinstance(X.category(), DrinfeldModules):
                raise NotImplementedError('Drinfeld modules must be in the same category')
            if category != X.category():
                raise NotImplementedError('category should be DrinfeldModules')
        base = category.base()
        super().__init__(X, Y, category=category, base=base, check=check)

    def _latex_(self):
        return f'\\text{{Set{{ }}of{{ }}Drinfeld{{ }}module{{ }}morphisms' \
                f'{{ }}from}}{latex(self.domain())}\\text{{{{ }}to{{ }}}}' \
                f'{self.codomain()}'

    def _repr_(self):
        return f'Set of Drinfeld module morphisms:\n' \
                f'  From: {self.domain()}\n' \
                f'  To:   {self.codomain()}'

    def __contains__(self, x):
        try:
            x = self(x)
            return True
        except (AttributeError, ValueError, TypeError):
            return False

    def _element_constructor_(self, *args, **kwds):
        # NOTE: This used to be self.element_class(self, ...), but this
        # would call __init__ instead of __classcall_private__. This
        # seems to work, but I don't know what I'm doing.
        return DrinfeldModuleMorphism(self, *args, **kwds)
