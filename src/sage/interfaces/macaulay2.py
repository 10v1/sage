r"""
Interface to Macaulay2

.. NOTE::

    You must have ``Macaulay2`` installed on your computer
    for this interface to work. Macaulay2 is not included with Sage,
    but you can obtain it from https://faculty.math.illinois.edu/Macaulay2/.
    No additional optional Sage packages are required.

Sage provides an interface to the Macaulay2 computational algebra
system. This system provides extensive functionality for commutative
algebra. You do not have to install any optional packages.

The Macaulay2 interface offers three pieces of functionality:

- ``macaulay2_console()`` -- A function that dumps you
  into an interactive command-line Macaulay2 session.

- ``macaulay2.eval(expr)`` -- Evaluation of arbitrary Macaulay2
  expressions, with the result returned as a string.

- ``macaulay2(expr)`` -- Creation of a Sage object that wraps a
  Macaulay2 object.  This provides a Pythonic interface to Macaulay2.  For
  example, if ``f = macaulay2(10)``, then ``f.gcd(25)`` returns the
  GCD of `10` and `25` computed using Macaulay2.

EXAMPLES::

    sage: macaulay2('3/5 + 7/11')       # optional - macaulay2
    68
    --
    55
    sage: f = macaulay2('f = i -> i^3') # optional - macaulay2
    sage: f                             # optional - macaulay2
    f
    sage: f(5)                          # optional - macaulay2
    125

    sage: R = macaulay2('ZZ/5[x,y,z]')  # optional - macaulay2
    sage: R                             # optional - macaulay2
    ZZ
    --[x, y, z]
     5
    sage: x = macaulay2('x')            # optional - macaulay2
    sage: y = macaulay2('y')            # optional - macaulay2
    sage: (x+y)^5                       # optional - macaulay2
     5    5
    x  + y
    sage: parent((x+y)^5)               # optional - macaulay2
    Macaulay2

The name of the variable to which a Macaulay2 element is assigned internally
can be passed as an argument. This is useful for types like polynomial rings
which acquire that name in Macaulay2::

    sage: R = macaulay2('QQ[x,y,z,w]', 'R')  # optional - macaulay2
    sage: R                                  # optional - macaulay2
    R

    sage: f = macaulay2('x^4 + 2*x*y^3 + x*y^2*w + x*y*z*w + x*y*w^2'    # optional - macaulay2
    ....:               '+ 2*x*z*w^2 + y^4 + y^3*w + 2*y^2*z*w + z^4 + w^4')
    sage: f                             # optional - macaulay2
     4       3    4    4      2     3                2           2         2    4
    x  + 2x*y  + y  + z  + x*y w + y w + x*y*z*w + 2y z*w + x*y*w  + 2x*z*w  + w
    sage: g = f * macaulay2('x+y^5')    # optional - macaulay2
    sage: print(g.factor())             # optional - macaulay2
      4       3    4    4      2     3                2           2         2    4   5
    (x  + 2x*y  + y  + z  + x*y w + y w + x*y*z*w + 2y z*w + x*y*w  + 2x*z*w  + w )(y  + x)

Use :meth:`eval` for explicit control over what is sent to the interpreter.
The argument is evaluated in Macaulay2 as is::

    sage: macaulay2.eval('compactMatrixForm')           # optional - macaulay2
    true
    sage: macaulay2.eval('compactMatrixForm = false;')  # optional - macaulay2
    sage: macaulay2.eval('matrix {{1, x^2+y}}')         # optional - macaulay2
    |     2     |
    | 1  x  + y |
    <BLANKLINE>
            1       2
    Matrix R  <--- R
    sage: macaulay2.eval('compactMatrixForm = true;')   # optional - macaulay2


AUTHORS:

- Kiran Kedlaya and David Roe (2006-02-05, during Sage coding sprint)
- William Stein (2006-02-09): inclusion in Sage; prompt uses regexp,
  calling of Macaulay2 functions via __call__.
- William Stein (2006-02-09): fixed bug in reading from file and
  improved output cleaning.
- Kiran Kedlaya (2006-02-12): added ring and ideal constructors,
  list delimiters, is_Macaulay2Element, sage_polystring,
  __floordiv__, __mod__, __iter__, __len__; stripped extra
  leading space and trailing newline from output.

.. TODO::

    Get rid of all numbers in output, e.g., in ideal function below.
"""

# ****************************************************************************
#       Copyright (C) 2006 Kiran S. Kedlaya <kedlaya@mit.edu>
#                          David Roe <roed@mit.edu>
#                          William Stein <wstein@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#  The full text of the GPL is available at:
#
#                  https://www.gnu.org/licenses/
# ****************************************************************************
from __future__ import print_function
from six import string_types

import os
import re

from sage.interfaces.expect import (Expect, ExpectElement, ExpectFunction,
                                    FunctionElement)
from sage.interfaces.interface import AsciiArtString
from sage.misc.multireplace import multiple_replace
from sage.interfaces.tab_completion import ExtraTabCompletion
from sage.docs.instancedoc import instancedoc


def remove_output_labels(s):
    r"""
    Remove output labels of Macaulay2 from a string.

    - s: output of Macaulay2

    - s: string

    Returns: the input string with `n` symbols removed from the beginning of
    each line, where `n` is the minimal number of spaces or symbols of
    Macaulay2 output labels (looking like 'o39 = ') present on every non-empty
    line.

    Return type: string

    .. note::

        If ``s`` consists of several outputs and their labels have
        different width, it is possible that some strings will have leading
        spaces (or maybe even pieces of output labels). However, this
        function will try not cut any messages.

    EXAMPLES::

        sage: from sage.interfaces.macaulay2 import remove_output_labels
        sage: output = 'o1 = QQ [x, y]\n\no1 : PolynomialRing\n'
        sage: remove_output_labels(output)
        'QQ [x, y]\n\nPolynomialRing\n'
    """
    label = re.compile("^o[0-9]+ (=|:) |^ *")
    lines = s.split("\n")
    matches = [label.match(l) for l in lines if l]
    if not matches:
        return s
    else:
        n = min(m.end() - m.start() for m in matches)
        return "\n".join(l[n:] for l in lines)


PROMPT = "_EGAS_ : "


class Macaulay2(ExtraTabCompletion, Expect):
    """
    Interface to the Macaulay2 interpreter.
    """
    def __init__(self, maxread=None, script_subdirectory=None,
                 logfile=None, server=None, server_tmpdir=None, command=None):
        """
        Initialize a Macaulay2 interface instance.

        We replace the standard input prompt with a strange one, so that
        we do not catch input prompts inside the documentation.

        We replace the standard input continuation prompt, which is
        just a bunch of spaces and cannot be automatically detected in a
        reliable way. This is necessary for allowing commands that occupy
        several strings.

        We also change the starting line number to make all the output
        labels to be of the same length. This allows correct stripping of
        the output of several commands.

        TESTS::

            sage: macaulay2 == loads(dumps(macaulay2))
            True
        """
        if command is None:
            command = os.getenv('SAGE_MACAULAY2_COMMAND') or 'M2'
        init_str = (
            # Prompt changing commands
            """ZZ#{Standard,Core#"private dictionary"#"InputPrompt"} = lineno -> "%s";""" % PROMPT +
            """ZZ#{Standard,Core#"private dictionary"#"InputContinuationPrompt"} = lineno -> "%s";""" % PROMPT +
            # Also prevent line wrapping in Macaulay2
            "printWidth = 0;" +
            # And make all output labels to be of the same width
            "lineNumber = 10^9;"
            # Assignment of internal expect variables.
            'sageAssign = (k, v) -> (if not instance(v, Sequence) then use v; k <- v);'
            )
        command = "%s --no-debug --no-readline --silent -e '%s'" % (command, init_str)
        Expect.__init__(self,
                        name = 'macaulay2',
                        prompt = PROMPT,
                        command = command,
                        server = server,
                        server_tmpdir = server_tmpdir,
                        script_subdirectory = script_subdirectory,
                        verbose_start = False,
                        logfile = logfile,
                        eval_using_file_cutoff=500)

    # Macaulay2 provides no "clear" function. However, Macaulay2 does provide
    # garbage collection; since expect automatically reuses variable names,
    # garbage collection in Sage properly sets up garbage collection in
    # Macaulay2.

    def __reduce__(self):
        """
        Used in serializing an Macaulay2 interface.

        EXAMPLES::

            sage: rlm2, t = macaulay2.__reduce__()
            sage: rlm2(*t)
            Macaulay2
        """
        return reduce_load_macaulay2, tuple([])

    def _read_in_file_command(self, filename):
        """
        Load and *execute* the content of ``filename`` in Macaulay2.

        INPUT:

        - filename: the name of the file to be loaded and executed
          (type: string)

        OUTPUT:

        Returns Macaulay2 command loading and executing commands in
        ``filename``, that is, ``'load "filename"'``.
        Return type: string

        TESTS::

            sage: filename = tmp_filename()
            sage: f = open(filename, "w")
            sage: _ = f.write("sage_test = 7;")
            sage: f.close()
            sage: command = macaulay2._read_in_file_command(filename)
            sage: macaulay2.eval(command)  # optional - macaulay2
            sage: macaulay2.eval("sage_test")  # optional - macaulay2
            7
            sage: import os
            sage: os.unlink(filename)
            sage: macaulay2._read_in_file_command("test")
            'load "test"'
            sage: macaulay2(10^10000) == 10^10000  # optional - macaulay2
            True
        """
        return 'load "%s"' % filename

    def eval(self, code, strip=True, **kwds):
        """
        Send the code x to the Macaulay2 interpreter and return the output
        as a string suitable for input back into Macaulay2, if possible.

        INPUT:

        - code -- str
        - strip -- ignored

        EXAMPLES::

            sage: macaulay2.eval("2+2") # optional - macaulay2
            4
        """
        code = code.strip()
        # TODO: in some cases change toExternalString to toString??
        ans = Expect.eval(self, code, strip=strip, **kwds).strip('\n')
        if strip:
            ans = remove_output_labels(ans)
        return AsciiArtString(ans)

    def restart(self):
        r"""
        Restart Macaulay2 interpreter.

        TESTS::

            sage: macaulay2.restart()  # optional - macaulay2
        """
        # If we allow restart to be called as a function, there will be
        # parasitic output
        self.eval("restart")

    def set_seed(self, seed=None):
        r"""
        Set the seed for Macaulay2 interpreter.

        INPUT:

        - ``seed`` -- number (default: ``None``). If ``None``, it
          is set to a random number.

        OUTPUT: the new seed

        EXAMPLES::

            sage: m = Macaulay2()                     # optional - macaulay2
            sage: m.set_seed(123456)                  # optional - macaulay2
            123456
            sage: [m.random(100) for _ in range(11)]  # optional - macaulay2
            [8, 29, 5, 22, 4, 32, 35, 57, 3, 95, 36]
        """
        if seed is None:
            seed = self.rand_seed()
        self.eval('setRandomSeed(%d)' % seed)
        self._seed = seed
        return seed

    def get(self, var):
        """
        Get the value of the variable ``var``.

        INPUT:

        - ``var`` - string; the name of the variable in Macaulay2

        OUTPUT: a string of the textual representation of the variable in
        Macaulay2

        EXAMPLES::

            sage: macaulay2.set("a", "2") # optional - macaulay2
            sage: macaulay2.get("a")      # optional - macaulay2
            2

        Note that the following syntax is used to obtain a
        ``Macaulay2Element`` instead::

            sage: a = macaulay2('2'); a   # optional - macaulay2
            2
            sage: type(a)                 # optional - macaulay2
            <class 'sage.interfaces.macaulay2.Macaulay2Element'>
        """
        return self.eval('print(%s)' % var, strip=False)

    def set(self, var, value):
        """
        Set the variable ``var`` to the given value.

        INPUT:

        - ``var`` - string; the name of the variable in Macaulay2
        - ``value`` - a string to evaluate

        EXAMPLES::

            sage: macaulay2.set("a", "1+1")  # optional - macaulay2
            sage: macaulay2.get("a")         # optional - macaulay2
            2

        TESTS:

        Check that internal expect variables do not acquire their global
        variable name and that ``use`` is invoked (:trac:`28303`)::

            sage: R = macaulay2('QQ[x, y]')  # indirect doctest, optional - macaulay2
            sage: R.net()                    # optional - macaulay2
            QQ[x, y]
            sage: S = R / macaulay2('ideal {x^2 - y}')         # optional - macaulay2
            sage: macaulay2.eval('class x === %s' % S.name())  # optional - macaulay2
            true
        """
        if re.match(r'sage\d+$', var):
            cmd = 'sageAssign(symbol %s,(%s));' % (var, value)
        else:
            cmd = '%s=(%s);' % (var,value)
        ans = Expect.eval(self, cmd, strip=False)
        if ans.find("stdio:") != -1:
            raise RuntimeError("Error evaluating Macaulay2 code.\nIN:%s\nOUT:%s" % (cmd, ans))

    def clear(self, var):
        """
        Clear the variable named ``var``.

        The interface automatically clears Macaulay2 elements when they fall
        out of use, so calling this method is usually not necessary.

        EXAMPLES::

            sage: macaulay2.eval('R = QQ[x,y];')  # optional - macaulay2
            sage: macaulay2.eval('net class R')   # optional - macaulay2
            PolynomialRing
            sage: macaulay2.clear('R')            # optional - macaulay2
            sage: macaulay2.eval('net class R')   # optional - macaulay2
            Symbol

        TESTS:

        Check that only internal variables get reused by the interface::

            sage: all(s.startswith('sage') for s in macaulay2._available_vars)  # optional - macaulay2
            True
        """
        if re.match(r'sage\d+$', var):
            self._available_vars.append(var)
        else:
            # this approach is also used by Macaulay2 itself in clearAll
            cmd = 'globalAssign(symbol {0},symbol {0});'.format(var)
            Expect.eval(self, cmd, strip=False)

    def _contains(self, v1, v2):
        """
        EXAMPLES::

            sage: a = macaulay2([3,4,5])  # optional - macaulay2
            sage: 0 in a, 2 in a, 3 in a  # optional - macaulay2, indirect doctest
            (True, True, False)
            sage: b = macaulay2('hashTable {"x" => 1, "y" => 2}')  # optional - macaulay2
            sage: 'x' in b, '"x"' in b    # optional - macaulay2, indirect doctest
            (False, True)
        """
        return self.eval("%s#?%s" % (v2, v1)) == self._true_symbol()

    def _object_class(self):
        """
        Return the class of Macaulay2 elements.

        EXAMPLES::

            sage: macaulay2._object_class()
            <class 'sage.interfaces.macaulay2.Macaulay2Element'>
        """
        return Macaulay2Element

    def _function_class(self):
        """
        Return the class of Macaulay2 functions.

        EXAMPLES::

            sage: macaulay2._function_class()
            <class 'sage.interfaces.macaulay2.Macaulay2Function'>
        """
        return Macaulay2Function

    def _function_element_class(self):
        """
        Return the class of partially-applied Macaulay2 functions.

        EXAMPLES::

            sage: macaulay2._function_element_class()
            <class 'sage.interfaces.macaulay2.Macaulay2FunctionElement'>
        """
        return Macaulay2FunctionElement

    def console(self):
        """
        Spawn a new M2 command-line session.

        EXAMPLES::

            sage: macaulay2.console()                    # not tested
            Macaulay 2, version 1.1
            with packages: Classic, Core, Elimination, IntegralClosure, LLLBases, Parsing, PrimaryDecomposition, SchurRings, TangentCone
            ...

        """
        macaulay2_console()

    def _install_hints(self):
        r"""

        TESTS::

            sage: m2 = Macaulay2(command='/wrongpath/M2')
            sage: m2('3+2')
            Traceback (most recent call last):
            ...
            TypeError: unable to start macaulay2 because the command '/wrongpath/M2 ...' failed: The command was not found or was not executable: /wrongpath/M2.
            <BLANKLINE>
                Your attempt to start Macaulay2 failed, either because you do not have
                have Macaulay2 installed, or because it is not configured correctly...
        """
        return r"""
    Your attempt to start Macaulay2 failed, either because you do not have
    have Macaulay2 installed, or because it is not configured correctly.

    - Macaulay2 is not included with Sage, but you can obtain it from
      https://faculty.math.illinois.edu/Macaulay2/.  No additional
      optional Sage packages are required.

    - If you have Macaulay2 installed, then perhaps it is not configured
      correctly. Sage assumes that you can start Macaulay2 with the command
      M2.

    - Alternatively, you can use the following command
      to point Sage to the correct command for your system.

          m2 = Macaulay2(command='/usr/local/bin/M2')

      or by setting the environment variable SAGE_MACAULAY2_COMMAND.
        """

    def _left_list_delim(self):
        """
        Returns the Macaulay2 left delimiter for lists.

        EXAMPLES::

            sage: macaulay2._left_list_delim()
            '{'
        """
        return '{'

    def _right_list_delim(self):
        """
        Returns the Macaulay2 right delimiter for lists.

        EXAMPLES::

            sage: macaulay2._right_list_delim()
            '}'
        """
        return '}'

    def _true_symbol(self):
        """
        Returns the Macaulay2 symbol for True.

        EXAMPLES::

            sage: macaulay2._true_symbol()
            'true'
        """
        return 'true'

    def _false_symbol(self):
        """
        Returns the Macaulay2 symbol for False.

        EXAMPLES::

            sage: macaulay2._false_symbol()
            'false'
        """
        return 'false'

    def _equality_symbol(self):
        """
        Returns the Macaulay2 symbol for equality.

        EXAMPLES::

            sage: macaulay2._false_symbol()
            'false'
        """
        return '=='

    def cputime(self, t=None):
        """
        EXAMPLES::

            sage: R = macaulay2("QQ[x,y]")  # optional - macaulay2
            sage: x,y = R.gens()            # optional - macaulay2
            sage: a = (x+y+1)^20            # optional - macaulay2
            sage: macaulay2.cputime()       # optional - macaulay2; random
            0.48393700000000001
        """
        _t = float(self.cpuTime()._sage_())
        if t:
            return _t - t
        else:
            return _t

    def version(self):
        """
        Returns the version of Macaulay2.

        EXAMPLES::

            sage: macaulay2.version() # optional - macaulay2
            (1, 1...
        """
        s = self.eval("version")
        r = re.compile("VERSION => (.*?)\n")
        s = r.search(s).groups()[0]
        return tuple(int(i) for i in s.split("."))

### Constructors

    def ideal(self, *gens):
        """
        Return the ideal generated by gens.

        INPUT:

        - gens -- list or tuple of Macaulay2 objects (or objects that can be
          made into Macaulay2 objects via evaluation)

        OUTPUT:

        the Macaulay2 ideal generated by the given list of gens

        EXAMPLES::

            sage: R2 = macaulay2.ring('QQ', '[x, y]'); R2            # optional - macaulay2
            QQ[x, y]
            sage: I = macaulay2.ideal( ('y^2 - x^3', 'x - y') ); I   # optional - macaulay2
                      3    2
            ideal (- x  + y , x - y)
            sage: J = I^3; J.gb().gens().transpose()                 # optional - macaulay2
            {-9} | y9-3y8+3y7-y6             |
            {-7} | xy6-2xy5+xy4-y7+2y6-y5    |
            {-5} | x2y3-x2y2-2xy4+2xy3+y5-y4 |
            {-3} | x3-3x2y+3xy2-y3           |

        """
        if len(gens) == 1 and isinstance(gens[0], (list, tuple)):
            gens = gens[0]
        gens2 = []
        for g in gens:
            if not isinstance(g, Macaulay2Element):
                gens2.append(self(g))
            else:
                gens2.append(g)
        return self('ideal {%s}'%(",".join([g.name() for g in gens2])))

    def ring(self, base_ring='ZZ', vars='[x]', order='Lex'):
        r"""
        Create a Macaulay2 polynomial ring.

        INPUT:

        - ``base_ring`` -- base ring (see examples below)
        - ``vars`` -- a tuple or string that defines the variable names
        - ``order`` -- string (default: 'Lex'); the monomial order

        OUTPUT: a Macaulay2 ring

        EXAMPLES:

        This is a ring in variables named ``a`` through ``d`` over the finite
        field of order 7, with graded reverse lex ordering::

            sage: R1 = macaulay2.ring('ZZ/7', '[a..d]', 'GRevLex')  # optional - macaulay2
            sage: R1.describe()  # optional - macaulay2
            ZZ
            --[a..d, Degrees => {4:1}, Heft => {1}, MonomialOrder => {MonomialSize => 16},
             7                                                       {GRevLex => {4:1}  }
                                                                     {Position => Up    }
            --------------------------------------------------------------------------------
            DegreeRank => 1]
            sage: R1.char()  # optional - macaulay2
            7

        This is a polynomial ring over the rational numbers::

            sage: R2 = macaulay2.ring('QQ', '[x, y]')  # optional - macaulay2
            sage: R2.describe()  # optional - macaulay2
            QQ[x..y, Degrees => {2:1}, Heft => {1}, MonomialOrder => {MonomialSize => 16},
                                                                     {Lex => 2          }
                                                                     {Position => Up    }
            --------------------------------------------------------------------------------
            DegreeRank => 1]

        TESTS::

            sage: macaulay2.ring('QQ', '[a_0..a_2,b..<d,f]').vars()     # optional - macaulay2
            | a_0 a_1 a_2 b c f |
        """
        return self.new(self._macaulay2_input_ring(base_ring, vars, order))

    def help(self, s):
        """
        EXAMPLES::

            sage: macaulay2.help("load")  # optional - macaulay2 - 1st call might be chatty...
            ...
            sage: macaulay2.help("load")  # optional - macaulay2
            load...
            ****...
            ...
              * "input" -- read Macaulay2 commands and echo
              * "notify" -- whether to notify the user when a file is loaded

        TESTS:

        Check that help also works for Macaulay2 keywords and variables
        (:trac:`28565`)::

            sage: from sage.repl.interpreter import get_test_shell
            sage: shell = get_test_shell()
            sage: shell.run_cell('macaulay2.help("try")')  # optional - macaulay2
            try -- catch an error
            ****...
            The object "try" is a keyword.

            sage: from sage.repl.interpreter import get_test_shell
            sage: shell = get_test_shell()
            sage: shell.run_cell('macaulay2.help("errorDepth")')  # optional - macaulay2
            errorDepth...
            The object "errorDepth" is an integer.
        """
        r = self.eval('help "%s"' % s)
        end = r.rfind("\n\nDIV")
        if end != -1:
            r = r[:end]
        return AsciiArtString(r)

    def _tab_completion(self):
        """
        Return a list of tab completions for Macaulay2.

        Returns dynamically built sorted list of commands obtained using
        Macaulay2 "apropos" command.
        Return type: list of strings

        TESTS::

            sage: names = macaulay2._tab_completion() # optional - macaulay2
            sage: 'ring' in names                 # optional - macaulay2
            True
            sage: macaulay2.eval("abcabc = 4")    # optional - macaulay2
            4
            sage: names = macaulay2._tab_completion() # optional - macaulay2
            sage: "abcabc" in names               # optional - macaulay2
            True
        """
        # Get all the names from Macaulay2 except numbered outputs like
        # o1, o2, etc. and automatic Sage variable names sage0, sage1, etc.
        # It is faster to get it back as a string.
        r = macaulay2.eval(r"""
            print toString select(
                apply(apropos "^[[:alnum:]]+$", toString),
                s -> not match("^(o|sage)[0-9]+$", s))
            """)
        # Now split this string into separate names
        r = sorted(r[1:-1].split(", "))
        # Macaulay2 sorts things like A, a, B, b, ...
        return r

    def use(self, R):
        """
        Use the Macaulay2 ring R.

        EXAMPLES::

            sage: R = macaulay2("QQ[x,y]")                  # optional - macaulay2
            sage: P = macaulay2("ZZ/7[symbol x, symbol y]") # optional - macaulay2
            sage: macaulay2("x").cls()._operator('===', P)  # optional - macaulay2
            true
            sage: macaulay2.use(R)                          # optional - macaulay2
            sage: macaulay2("x").cls()._operator('===', R)  # optional - macaulay2
            true
        """
        R = self(R)
        self.eval("use %s;" % R.name(), strip=False)

    def new_from(self, type, value):
        """
        Return a new ``Macaulay2Element`` of type ``type`` constructed from
        ``value``.

        EXAMPLES::

            sage: l = macaulay2.new_from("MutableList", [1,2,3]) # optional - macaulay2
            sage: l                                              # optional - macaulay2
            MutableList{...3...}
            sage: list(l)                                        # optional - macaulay2
            [1, 2, 3]

        """
        type = self(type)
        value = self(value)
        return self.new("new %s from %s"%(type.name(), value.name()))

    def _macaulay2_input_ring(self, base_ring, vars, order='GRevLex'):
        """
        Build a string representation of a polynomial ring which can be used as
        Macaulay2 input.

        TESTS::

            sage: R = GF(101)['x']
            sage: macaulay2._macaulay2_input_ring(R.base_ring(), R.gens(), 'Lex')   # optional - macaulay2
            'sage...[symbol x, MonomialSize=>16, MonomialOrder=>Lex]'
        """
        if not isinstance(base_ring, string_types):
            base_ring = self(base_ring).name()

        varstr = str(vars)[1:-1].rstrip(',')
        r = re.compile(r"(?<=,)|(?<=\.\.<)|(?<=\.\.)(?!<)")
        varstr = "symbol " + r.sub("symbol ", varstr)
        return '%s[%s, MonomialSize=>16, MonomialOrder=>%s]' % (base_ring, varstr,
                                                                order)


@instancedoc
class Macaulay2Element(ExtraTabCompletion, ExpectElement):
    """
    Instances of this class represent objects in Macaulay2.

    Using the method :meth:`sage` we can translate some of them to
    SageMath objects:

    .. automethod:: _sage_
    """
    def _latex_(self):
        r"""
        EXAMPLES::

            sage: m = macaulay2('matrix {{1,2},{3,4}}') # optional - macaulay2
            sage: m                                     # optional - macaulay2
            | 1 2 |
            | 3 4 |
            sage: latex(m) # optional - macaulay2
            \begin{pmatrix}...1...2...3...4...\end{pmatrix}
        """
        s = self.tex().external_string().strip('"').strip('$').replace('\\\\','\\')
        s = s.replace(r"\bgroup","").replace(r"\egroup","")
        return s

    def __iter__(self):
        """
        EXAMPLES::

            sage: l = macaulay2([1,2,3]) # optional - macaulay2
            sage: list(iter(l))          # optional - macaulay2
            [1, 2, 3]
        """
        for i in range(len(self)):  # zero-indexed!
            yield self[i]

    def __str__(self):
        """
        EXAMPLES::

            sage: R = macaulay2("QQ[x,y,z]/(x^3-y^3-z^3)") # optional - macaulay2
            sage: x = macaulay2('x')                       # optional - macaulay2
            sage: y = macaulay2('y')                       # optional - macaulay2
            sage: str(x+y)                                 # optional - macaulay2
            x + y
            sage: str(macaulay2("QQ[x,y,z]"))              # optional - macaulay2
            QQ[x, y, z]
            sage: str(macaulay2("QQ[x,y,z]/(x+y+z)"))      # optional - macaulay2
            QQ[x, y, z]
            -----------
             x + y + z
        """
        P = self._check_valid()
        return P.get(self._name)

    def _repr_(self):
        """
        EXAMPLES::

            sage: repr(macaulay2('1..25'))  # optional - macaulay2
            (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
            --------------------------------------------------------------------------------
            23, 24, 25)
            sage: str(macaulay2('1..25'))  # optional - macaulay2
            (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25)
        """
        from sage.typeset.ascii_art import empty_ascii_art
        P = self.parent()
        return P.eval('print(wrap(%d,"-",net %s))'
                      % (empty_ascii_art._terminal_width(), self._name),
                      strip=False)

    def external_string(self):
        """
        EXAMPLES::

           sage: R = macaulay2("QQ[symbol x, symbol y]")  # optional - macaulay2
           sage: R.external_string()                      # optional - macaulay2
           'QQ(monoid[x..y, Degrees => {2:1}, Heft => {1}, MonomialOrder => VerticalList{MonomialSize => 32, GRevLex => {2:1}, Position => Up}, DegreeRank => 1])'
        """
        P = self._check_valid()
        code = 'toExternalString(%s)'%self.name()
        X = P.eval(code, strip=True)

        if 'stdio:' in X:
            if 'to external string' in X:
                return P.eval('%s'%self.name())
            raise RuntimeError("Error evaluating Macaulay2 code.\nIN:%s\nOUT:%s"%(code, X))

        s = multiple_replace({'\r':'', '\n':' '}, X)
        return s

    def name(self, new_name=None):
        """
        Get or change the name of this Macaulay2 element.

        INPUT:

        - ``new_name`` -- string (default: ``None``). If ``None``, return the
          name of this element; else return a new object identical to ``self``
          whose name is ``new_name``.

        Note that this can overwrite existing variables in the system.

        EXAMPLES::

            sage: S = macaulay2(QQ['x,y'])          # optional - macaulay2
            sage: S.name()                          # optional - macaulay2
            'sage...'
            sage: R = S.name("R")                   # optional - macaulay2
            sage: R.name()                          # optional - macaulay2
            'R'
            sage: R.vars().cokernel().resolution()  # optional - macaulay2
             1      2      1
            R  <-- R  <-- R  <-- 0
            <BLANKLINE>
            0      1      2      3

        The name can also be given at definition::

            sage: A = macaulay2(ZZ['x,y,z'], name='A')  # optional - macaulay2
            sage: A.name()                              # optional - macaulay2
            'A'
            sage: A^1                                   # optional - macaulay2
             1
            A
        """
        if new_name is None:
            return self._name
        if not isinstance(new_name, string_types):
            raise TypeError("new_name must be a string")

        P = self.parent()
        # First release self, so that new_name becomes the initial reference to
        # its value.  This is needed to change the name of a PolynomialRing.
        # NOTE: This does not work if self._name is not the initial reference.
        cmd = """(() -> (
            m := lookup(GlobalReleaseHook, class {0});
            if m =!= null then m(symbol {0}, {0});
            {1} = {0};
            ))()""".format(self._name, new_name)
        ans = P.eval(cmd)
        if ans.find("stdio:") != -1:
            raise RuntimeError("Error evaluating Macaulay2 code.\n"
                               "IN:%s\nOUT:%s" % (cmd, ans))
        return P._object_class()(P, new_name, is_name=True)

    def __len__(self):
        """
        EXAMPLES::

            sage: l = macaulay2([1,2,3])  # optional - macaulay2
            sage: len(l)                  # optional - macaulay2
            3
            sage: type(_)                 # optional - macaulay2
            <... 'int'>
        """
        self._check_valid()
        return int(self.parent()("#%s"%self.name()))

    def __getitem__(self, n):
        """
        EXAMPLES::

            sage: l = macaulay2([1,2,3])  # optional - macaulay2
            sage: l[0]                    # optional - macaulay2
            1
        """
        self._check_valid()
        n = self.parent()(n)
        return self.parent().new('%s # %s'%(self.name(), n.name()))

    def __setitem__(self, index, value):
        """
        EXAMPLES::

            sage: l = macaulay2.new_from("MutableList", [1,2,3]) # optional - macaulay2
            sage: l[0] = 4               # optional - macaulay2
            sage: list(l)                # optional - macaulay2
            [4, 2, 3]

        """
        P = self.parent()
        index = P(index)
        value = P(value)
        res = P.eval("%s # %s = %s"%(self.name(), index.name(), value.name()))
        if "assignment attempted to element of immutable list" in res:
            raise TypeError("item assignment not supported")

    def __call__(self, x):
        """
        EXAMPLES::

            sage: R = macaulay2("QQ[x, y]")     # optional - macaulay2
            sage: x,y = R.gens()                # optional - macaulay2
            sage: I = macaulay2.ideal(x*y, x+y) # optional - macaulay2
            sage: gb = macaulay2.gb             # optional - macaulay2
            sage: gb(I)                         # optional - macaulay2
            GroebnerBasis[status: done; S-pairs encountered up to degree 1]
        """
        self._check_valid()
        P = self.parent()
        r = P(x)
        return P('%s %s'%(self.name(), r.name()))

    def __floordiv__(self, x):
        """
        Quotient of division of self by other.  This is denoted //.

        EXAMPLES::

            sage: R.<x,y> = GF(7)[]

        Now make the M2 version of R, so we can coerce elements of R to M2::

            sage: _ = macaulay2(R)                       # optional - macaulay2
            sage: h = macaulay2((x^3 + 2*y^2*x)^7); h    # optional - macaulay2
             21     7 14
            x   + 2x y
            sage: h1 = macaulay2(x^2 + 2*y*x)            # optional - macaulay2
            sage: h2 = macaulay2(x^3 + 2*y*x)            # optional - macaulay2
            sage: u = h // [h1,h2]                       # optional - macaulay2
            sage: h == u[0]*h1 + u[1]*h2 + (h % [h1,h2]) # optional - macaulay2
            True
        """
        if isinstance(x, (list, tuple)):
            y = self.parent(x)
            z = self.parent().new('%s // matrix{%s}'%(self.name(), y.name()))
            return list(z.entries().flatten())
        else:
            return self.parent().new('%s // %s'%(self.name(), x.name()))

    def __mod__(self, x):
        """
        Remainder of division of self by other.  This is denoted %.

        EXAMPLES::

            sage: R.<x,y> = GF(7)[]

        Now make the M2 version of R, so we can coerce elements of R to M2::

            sage: _ = macaulay2(R)                          # optional - macaulay2
            sage: h = macaulay2((x^3 + 2*y^2*x)^7); h       # optional - macaulay2
             21     7 14
            x   + 2x y
            sage: h1 = macaulay2(x^2 + 2*y*x)               # optional - macaulay2
            sage: h2 = macaulay2(x^3 + 2*y*x)               # optional - macaulay2
            sage: h % [h1,h2]                               # optional - macaulay2
            -3x*y
            sage: u = h // [h1,h2]                          # optional - macaulay2
            sage: h == u[0]*h1 + u[1]*h2 + (h % [h1,h2])    # optional - macaulay2
            True
        """
        if isinstance(x, (list, tuple)):
            y = self.parent(x)
            return self.parent().new('%s %% matrix{%s}'%(self.name(), y.name()))
        if not isinstance(x, Macaulay2Element):
            x = self.parent(x)
        return self.parent().new('%s %% %s'%(self.name(), x.name()))

    def __bool__(self):
        """
        Return whether this Macaulay2 element is not ``False`` or not ``0``.

        EXAMPLES::

            sage: a = macaulay2(0)  # optional - macaulay2
            sage: a == 0            # optional - macaulay2
            True
            sage: bool(a)           # optional - macaulay2
            False

        TESTS:

        Check that :trac:`28705` is fixed::

            sage: t = macaulay2(True); t     # optional - macaulay2
            true
            sage: bool(t)                    # optional - macaulay2
            True
            sage: bool(macaulay2('false'))   # optional - macaulay2
            False
            sage: bool(macaulay2('"a"'))     # optional - macaulay2
            True
        """
        P = self.parent()
        return P.eval('{0}===false or {0}==0'.format(self._name)) != 'true'

    __nonzero__ = __bool__

    def sage_polystring(self):
        """
        If this Macaulay2 element is a polynomial, return a string
        representation of this polynomial that is suitable for
        evaluation in Python.  Thus ``*`` is used for multiplication
        and ``**`` for exponentiation.   This function is primarily
        used internally.

        EXAMPLES::

            sage: R = macaulay2.ring('QQ','(x,y)')               # optional - macaulay2
            sage: f = macaulay2('x^3 + 3*y^11 + 5')              # optional - macaulay2
            sage: print(f)                                       # optional - macaulay2
             3     11
            x  + 3y   + 5
            sage: f.sage_polystring()                            # optional - macaulay2
            'x**3+3*y**11+5'
        """
        return self.external_string().replace('^','**')

    def structure_sheaf(self):
        """
        EXAMPLES::

            sage: S = macaulay2('QQ[a..d]')                     # optional - macaulay2
            sage: R = S / macaulay2('a^3 + b^3 + c^3 + d^3')    # optional - macaulay2
            sage: X = R.Proj().name('X')                        # optional - macaulay2
            sage: X.structure_sheaf()                           # optional - macaulay2
            doctest:...: DeprecationWarning: The function `structure_sheaf` is deprecated. Use `self.sheaf()` instead.
            See https://trac.sagemath.org/27848 for details.
            OO
              X
            sage: X.sheaf()                                     # optional - macaulay2
            OO
              X
        """
        from sage.misc.superseded import deprecation
        deprecation(27848, 'The function `structure_sheaf` is deprecated. Use `self.sheaf()` instead.')
        return self.parent()('OO_%s'%self.name())

    def substitute(self, *args, **kwds):
        """
        Note that we have to override the substitute method so that we get
        the default one from Macaulay2 instead of the one provided by Element.

        EXAMPLES::

            sage: R = macaulay2("QQ[x]")            # optional - macaulay2
            sage: P = macaulay2("ZZ/7[symbol x]")   # optional - macaulay2
            sage: x, = R.gens()                     # optional - macaulay2
            sage: a = x^2 + 1                       # optional - macaulay2
            sage: a = a.substitute(P)               # optional - macaulay2
            sage: a.sage().parent()                 # optional - macaulay2
            Univariate Polynomial Ring in x over Finite Field of size 7

        """
        return self.__getattr__("substitute")(*args, **kwds)

    subs = substitute

    def _tab_completion(self):
        """
        Return a list of tab completions for ``self``.

        Returns dynamically built sorted list of commands obtained using
        Macaulay2 "methods" command. All returned functions can take ``self``
        as their first argument

        Return type: list of strings

        TESTS::

            sage: a = macaulay2("QQ[x,y]")      # optional - macaulay2
            sage: traits = a._tab_completion()  # optional - macaulay2
            sage: "generators" in traits        # optional - macaulay2
            True

        The implementation of this function does not set or change global
        variables::

            sage: a.dictionary()._operator('#?', '"r"')  # optional - macaulay2
            false
        """
        # It is possible, that these are not all possible methods, but
        # there are still plenty and at least there are no definitely
        # wrong ones...
        r = self.parent().eval(
            """(() -> (
            currentClass := class %s;
            total := {};
            while true do (
                -- Select methods with first argument of the given class
                r := select(methods currentClass, s -> s_1 === currentClass);
                -- Get their names as strings
                r = apply(r, s -> toString s_0);
                -- Keep only alpha-numeric ones
                r = select(r, s -> match("^[[:alnum:]]+$", s));
                -- Add to existing ones
                total = total | select(r, s -> not any(total, e -> e == s));
                if parent currentClass === currentClass then break;
                currentClass = parent currentClass;
                );
            print toString total
            ))()""" % self.name())
        r = sorted(r[1:-1].split(", "))
        return r

    def cls(self):
        """
        Since class is a keyword in Python, we have to use cls to call
        Macaulay2's class.  In Macaulay2, class corresponds to Sage's
        notion of parent.

        EXAMPLES::

            sage: macaulay2(ZZ).cls()  # optional - macaulay2
            Ring

        """
        return self.parent()("class %s"%self.name())

    ##########################
    #Aliases for M2 operators#
    ##########################
    def dot(self, x):
        """
        EXAMPLES::

            sage: d = macaulay2.new("MutableHashTable") # optional - macaulay2
            sage: d["k"] = 4                            # optional - macaulay2
            sage: d.dot("k")                            # optional - macaulay2
            4
        """
        parent = self.parent()
        x = parent(x)
        return parent("%s.%s" % (self.name(), x))

    def _operator(self, opstr, x):
        """
        Returns the infix binary operation specified by opstr applied
        to self and x.

        EXAMPLES::

            sage: a = macaulay2("3")     # optional - macaulay2
            sage: a._operator("+", a)    # optional - macaulay2
            6
            sage: a._operator("*", a)    # optional - macaulay2
            9
        """
        parent = self.parent()
        x = parent(x)
        return parent("%s%s%s"%(self.name(), opstr, x.name()))

    def sharp(self, x):
        """
        EXAMPLES::

            sage: a = macaulay2([1,2,3]) # optional - macaulay2
            sage: a.sharp(0)             # optional - macaulay2
            1
        """
        return self._operator("#", x)

    def starstar(self, x):
        """
        The binary operator ``**`` in Macaulay2 is usually used for tensor
        or Cartesian power.

        EXAMPLES::

            sage: a = macaulay2([1,2]).set()  # optional - macaulay2
            sage: a.starstar(a)               # optional - macaulay2
            set {(1, 1), (1, 2), (2, 1), (2, 2)}

        """
        return self._operator("**", x)

    def underscore(self, x):
        """
        EXAMPLES::

            sage: a = macaulay2([1,2,3])  # optional - macaulay2
            sage: a.underscore(0)         # optional - macaulay2
            1
        """
        return self._operator("_", x)

    ####################
    #Conversion to Sage#
    ####################
    def _sage_(self):
        r"""
        EXAMPLES::

            sage: macaulay2(ZZ).sage()         # optional - macaulay2, indirect doctest
            Integer Ring
            sage: macaulay2(QQ).sage()         # optional - macaulay2
            Rational Field

            sage: macaulay2(2).sage()          # optional - macaulay2
            2
            sage: macaulay2(1/2).sage()        # optional - macaulay2
            1/2
            sage: macaulay2(2/1).sage()        # optional - macaulay2
            2
            sage: _.parent()                   # optional - macaulay2
            Rational Field
            sage: macaulay2([1,2,3]).sage()    # optional - macaulay2
            [1, 2, 3]

            sage: m = matrix([[1,2],[3,4]])
            sage: macaulay2(m).sage()          # optional - macaulay2
            [1 2]
            [3 4]

            sage: D = macaulay2('hashTable {4 => 1, 2 => 3}')  # optional - macaulay2
            sage: D.pairs()                    # optional - macaulay2
            {(4, 1), (2, 3)}
            sage: D.sage() == {4: 1, 2: 3}    # optional - macaulay2
            True

            sage: macaulay2(QQ['x,y']).sage()       # optional - macaulay2
            Multivariate Polynomial Ring in x, y over Rational Field
            sage: macaulay2(QQ['x']).sage()         # optional - macaulay2
            Univariate Polynomial Ring in x over Rational Field
            sage: macaulay2(GF(7)['x,y']).sage()    # optional - macaulay2
            Multivariate Polynomial Ring in x, y over Finite Field of size 7

            sage: macaulay2(GF(7)).sage()          # optional - macaulay2
            Finite Field of size 7
            sage: macaulay2(GF(49, 'a')).sage()    # optional - macaulay2
            Finite Field in a of size 7^2

            sage: R.<x,y> = QQ[]
            sage: macaulay2(x^2+y^2+1).sage()      # optional - macaulay2
            x^2 + y^2 + 1

            sage: R = macaulay2("QQ[x,y]")         # optional - macaulay2
            sage: I = macaulay2("ideal (x,y)")     # optional - macaulay2
            sage: I.sage()                         # optional - macaulay2
            Ideal (x, y) of Multivariate Polynomial Ring in x, y over Rational Field

            sage: macaulay2("x = symbol x")           # optional - macaulay2
            x
            sage: macaulay2("QQ[x_0..x_25]").sage()    # optional - macaulay2
            Multivariate Polynomial Ring in x_0, x_1,..., x_25 over Rational Field

            sage: S = ZZ['x,y'].quotient('x^2-y')
            sage: macaulay2(S).sage() == S         # optional - macaulay2
            True
            sage: S = GF(101)['x,y'].quotient('x^2-y')
            sage: macaulay2(S).sage() == S         # optional - macaulay2
            True

            sage: R = GF(13)['a,b']['c,d']
            sage: macaulay2(R).sage() == R  # optional - macaulay2
            True
            sage: macaulay2('a^2 + c').sage() == R('a^2 + c')  # optional - macaulay2
            True
            sage: macaulay2.substitute('a', R).sage().parent() is R  # optional - macaulay2
            True

            sage: R = macaulay2("QQ^2")  # optional - macaulay2
            sage: R.sage()               # optional - macaulay2
            Vector space of dimension 2 over Rational Field

            sage: macaulay2("vector {4_QQ, 2}").sage()  # optional - macaulay2
            (4, 2)
            sage: _.parent()                            # optional - macaulay2
            Vector space of dimension 2 over Rational Field

            sage: m = macaulay2('"hello"')  # optional - macaulay2
            sage: m.sage()                  # optional - macaulay2
            'hello'

            sage: gg = macaulay2.needsPackage('"Graphs"') # optional - macaulay2
            sage: g = macaulay2.barbellGraph(3)         # optional - macaulay2
            sage: g.sage()                              # optional - macaulay2
            Graph on 6 vertices
            sage: g.sage().edges(labels=False)          # optional - macaulay2
            [(0, 1), (0, 2), (1, 2), (2, 3), (3, 4), (3, 5), (4, 5)]

            sage: d = 'digraph ({{1,2},{2,1},{3,1}}, EntryMode => "edges")'
            sage: g = macaulay2(d)                      # optional - macaulay2
            sage: g.sage()                              # optional - macaulay2
            Digraph on 3 vertices
            sage: g.sage().edges(labels=False)          # optional - macaulay2
            [(1, 2), (2, 1), (3, 1)]

        Chain complexes and maps of chain complexes can be converted::

            sage: R = ZZ['a,b,c']
            sage: C = macaulay2(ideal(R.gens())).resolution()  # optional - macaulay2
            sage: ascii_art(C.sage())                          # optional - macaulay2
                                      [-b  0 -c]       [ c]
                                      [ a -c  0]       [ a]
                        [a b c]       [ 0  b  a]       [-b]
             0 <-- C_0 <-------- C_1 <----------- C_2 <----- C_3 <-- 0
            sage: F = C.dot('dd')  # optional - macaulay2
            sage: G = F.sage()     # optional - macaulay2
            sage: G.in_degree(2)   # optional - macaulay2
            [-b  0 -c]
            [ a -c  0]
            [ 0  b  a]
            sage: F.underscore(2).sage() == G.in_degree(2)  # optional - macaulay2
            True
            sage: (F^2).sage()     # optional - macaulay2
            Chain complex morphism:
              From: Chain complex with at most 4 nonzero terms over Multivariate Polynomial Ring in a, b, c over Integer Ring
              To:   Chain complex with at most 4 nonzero terms over Multivariate Polynomial Ring in a, b, c over Integer Ring

        Quotient rings in Macaulay2 inherit variable names from the ambient
        ring, so we mimic this behaviour in Sage::

            sage: R = macaulay2("ZZ/7[x,y]")            # optional - macaulay2
            sage: I = macaulay2("ideal (x^3 - y^2)")    # optional - macaulay2
            sage: (R/I).gens()                          # optional - macaulay2
            {x, y}
            sage: (R/I).sage().gens()                   # optional - macaulay2
            (x, y)

        Elements of quotient rings::

            sage: x, y = (R/I).gens()                   # optional - macaulay2
            sage: f = ((x^3 + 2*y^2*x)^7).sage(); f     # optional - macaulay2
            2*x*y^18 + y^14
            sage: f.parent()                            # optional - macaulay2
            Quotient of Multivariate Polynomial Ring in x, y over Finite Field of size 7 by the ideal (x^3 - y^2)

        """
        repr_str = str(self)
        cls_str = str(self.cls())
        cls_cls_str = str(self.cls().cls())

        if repr_str == "ZZ":
            from sage.rings.all import ZZ
            return ZZ
        elif repr_str == "QQ":
            from sage.rings.all import QQ
            return QQ

        if cls_cls_str == "Type":
            if cls_str == "List":
                return [entry._sage_() for entry in self]
            elif cls_str == "Matrix":
                base_ring = self.ring()._sage_()
                return self._matrix_(base_ring)
            elif cls_str == 'HashTable':
                return {x._sage_(): y._sage_() for (x, y) in self.pairs()}
            elif cls_str == "Ideal":
                parent = self.ring()._sage_()
                gens = self.gens().entries().flatten()._sage_()
                return parent.ideal(*gens)
            elif cls_str == "QuotientRing":
                #Handle the ZZ/n case
                ambient = self.ambient()
                if ambient.external_string() == 'ZZ':
                    from sage.rings.all import ZZ, GF
                    external_string = self.external_string()
                    zz, n = external_string.split("/")

                    #Note that n must be prime since it is
                    #coming from Macaulay 2
                    return GF(ZZ(n))
                else:
                    ambient_ring = ambient._sage_()
                    ideal = self.ideal()._sage_()
                    return ambient_ring.quotient(ideal, names=ambient_ring.variable_names())
            elif cls_str == "PolynomialRing":
                from sage.rings.all import PolynomialRing
                from sage.rings.polynomial.term_order import inv_macaulay2_name_mapping

                #Get the base ring
                base_ring = self.coefficientRing()._sage_()

                #Get a string list of generators
                gens = str(self.gens().toString())[1:-1]

                # Check that we are dealing with default degrees, i.e. 1's.
                if self.options().sharp("Degrees").any("x -> x != {1}")._sage_():
                    raise ValueError("cannot convert Macaulay2 polynomial ring with non-default degrees to Sage")
                #Handle the term order
                external_string = self.external_string()
                order = None
                if "MonomialOrder" not in external_string:
                    order = "degrevlex"
                else:
                    for order_name in inv_macaulay2_name_mapping:
                        if order_name in external_string:
                            order = inv_macaulay2_name_mapping[order_name]
                if len(gens) > 1 and order is None:
                    raise ValueError("cannot convert Macaulay2's term order to a Sage term order")

                return PolynomialRing(base_ring, order=order, names=gens)
            elif cls_str == "GaloisField":
                from sage.rings.all import ZZ, GF
                gf, n = repr_str.split(" ")
                n = ZZ(n)
                if n.is_prime():
                    return GF(n)
                else:
                    gen = str(self.gens())[1:-1]
                    return GF(n, gen)
            elif cls_str == "Boolean":
                if repr_str == "true":
                    return True
                elif repr_str == "false":
                    return False
            elif cls_str == "String":
                return str(repr_str)
            elif cls_str == "Module":
                from sage.modules.all import FreeModule
                if self.isFreeModule()._sage_():
                    ring = self.ring()._sage_()
                    rank = self.rank()._sage_()
                    return FreeModule(ring, rank)
            elif cls_str in ("Graph", "Digraph"):
                if cls_str == "Graph":
                    from sage.graphs.graph import Graph
                    graph_cls = Graph
                else:
                    from sage.graphs.digraph import DiGraph
                    graph_cls = DiGraph
                adj_mat = self.adjacencyMatrix().sage()
                g = graph_cls(adj_mat, format='adjacency_matrix')
                g.relabel(self.vertices())
                return g
            elif cls_str == "ChainComplex":
                from sage.homology.chain_complex import ChainComplex
                ring = self.ring()._sage_()
                dd = self.dot('dd')
                degree = dd.degree()._sage_()
                a = self.min()._sage_()
                b = self.max()._sage_()
                matrices = {i: dd.underscore(i)._matrix_(ring)
                            for i in range(a, b+1)}
                return ChainComplex(matrices, degree=degree)
            elif cls_str == "ChainComplexMap":
                from sage.homology.chain_complex_morphism import ChainComplexMorphism
                ring = self.ring()._sage_()
                source = self.source()
                a = source.min()._sage_()
                b = source.max()._sage_()
                degree = self.degree()._sage_()
                matrices = {i: self.underscore(i)._matrix_(ring)
                            for i in range(a, b+1)}
                C = source._sage_()
                # in Sage, chain complex morphisms are degree-preserving,
                # so we shift the degrees of the target
                D = self.target()._operator(' ', '[%s]' % degree)._sage_()
                return ChainComplexMorphism(matrices, C, D)
        else:
            #Handle the integers and rationals separately
            if cls_str == "ZZ":
                from sage.rings.all import ZZ
                return ZZ(repr_str)
            elif cls_str == "QQ":
                from sage.rings.all import QQ
                repr_str = self.external_string()
                if "/" not in repr_str:
                    repr_str = repr_str + "/1"
                return QQ(repr_str)

            m2_parent = self.cls()
            parent = m2_parent._sage_()

            if cls_cls_str in ("PolynomialRing", "QuotientRing"):
                return parent(self.external_string())
            elif cls_cls_str == "Module":
                entries = self.entries()._sage_()
                return parent._element_constructor_(entries)

        from sage.misc.sage_eval import sage_eval
        try:
            return sage_eval(repr_str)
        except Exception:
            raise NotImplementedError("cannot convert %s to a Sage object"%repr_str)

    from sage.misc.superseded import deprecated_function_alias
    to_sage = deprecated_function_alias(27848, ExpectElement.sage)

    def _matrix_(self, R):
        r"""
        If ``self`` is a Macaulay2 matrix, return the corresponding Sage matrix
        over the Sage ring ``R``.

        INPUT:

        - ``R`` - ring to coerce into

        OUTPUT: matrix

        EXAMPLES::

            sage: A = macaulay2('matrix {{1,2},{3,4}}')  # optional - macaulay2
            sage: matrix(QQ, A)                          # optional - macaulay2, indirect doctest
            [1 2]
            [3 4]

        TESTS:

        Check that degenerate matrix dimensions are preserved (:trac:`28591`)::

            sage: m = macaulay2('matrix {{},{}}')  # optional - macaulay2
            sage: matrix(ZZ, m).dimensions()  # optional - macaulay2
            (2, 0)
            sage: matrix(ZZ, m.transpose()).dimensions()  # optional - macaulay2
            (0, 2)
        """
        from sage.matrix.all import matrix
        m = matrix(R, self.entries()._sage_())
        if not m.nrows():
            return matrix(R, 0, self.numcols()._sage_())
        return m


@instancedoc
class Macaulay2Function(ExpectFunction):
    """
    TESTS::

        sage: gb = macaulay2.gb  # optional - macaulay2
        sage: type(gb)           # optional - macaulay2
        <class 'sage.interfaces.macaulay2.Macaulay2Function'>
        sage: gb._name           # optional - macaulay2
        'gb'
    """

    def _instancedoc_(self):
        """
        EXAMPLES::

            sage: print(macaulay2.load.__doc__)  # optional - macaulay2
            nodetex,noreplace
            load...
            ****...
            ...
              * "input" -- read Macaulay2 commands and echo
              * "notify" -- whether to notify the user when a file is loaded

        TESTS:

        Check that detex is disabled, so that the output does not get
        reformatted (:trac:`28565`)::

            sage: from sage.repl.interpreter import get_test_shell
            sage: shell = get_test_shell()
            sage: shell.run_cell('macaulay2.matrix?')  # optional - macaulay2
            ...
            +----------------------------+
            |i1 : matrix{{1,2,3},{4,5,6}}|
            |                            |
            |o1 = | 1 2 3 |              |
            |     | 4 5 6 |              |
            |                            |
            |              2        3    |
            |o1 : Matrix ZZ  <--- ZZ     |
            +----------------------------+
            ...
        """
        r = self._parent.help(self._name)
        return AsciiArtString('nodetex,noreplace\n' + r)

    def _sage_src_(self):
        """
        EXAMPLES::

            sage: macaulay2.gb._sage_src_()  # optional - macaulay2
            -- code for method: gb(Ideal)...
            -- code for method: gb(Matrix)...
            ...
        """
        return self._parent.eval('code methods %s' % self._name)


@instancedoc
class Macaulay2FunctionElement(FunctionElement):
    def _instancedoc_(self):
        """
        TESTS:

        Since :trac:`28565`, the help output includes all documentation nodes
        that can take ``self._obj`` as first argument. This also checks that
        detex is disabled, so that the output does not get reformatted. ::

            sage: from sage.repl.interpreter import get_test_shell
            sage: shell = get_test_shell()
            sage: shell.run_cell('I = macaulay2("ideal {4}")')  # optional - macaulay2
            sage: shell.run_cell('I.resolution?')  # optional - macaulay2
            Signature:...
            Docstring:
            resolution -- projective resolution
            ****...
            <BLANKLINE>
            resolution(Ideal) -- compute a projective resolution of...
            ****...
            |      1      4      6      4      1      |
            |o3 = R  <-- R  <-- R  <-- R  <-- R  <-- 0|
            |                                         |
            |     0      1      2      3      4      5|
            ...
        """
        P = self._obj.parent()
        r = P.eval('help prepend({0}, select(methods {0}, m->'
                   'instance({1}, m#1)))'.format(self._name, self._obj._name))
        end = r.rfind("\n\nDIV")
        if end != -1:
            r = r[:end]
        return AsciiArtString('nodetex,noreplace\n' + r)

    def _sage_src_(self):
        """
        EXAMPLES::

            sage: m = macaulay2('matrix {{4,6}}')  # optional - macaulay2
            sage: m.resolution._sage_src_()  # optional - macaulay2
            -- code for method: resolution(Matrix)...
        """
        return self._obj.parent().eval(
            'code select(methods %s, m->instance(%s, m#1))'
            % (self._name, self._obj._name))


def is_Macaulay2Element(x):
    """
    EXAMPLES::

        sage: from sage.interfaces.macaulay2 import is_Macaulay2Element
        sage: is_Macaulay2Element(2)              # optional - macaulay2
        False
        sage: is_Macaulay2Element(macaulay2(2))   # optional - macaulay2
        True
    """
    return isinstance(x, Macaulay2Element)

# An instance
macaulay2 = Macaulay2()


def macaulay2_console():
    """
    Spawn a new M2 command-line session.

    EXAMPLES::

        sage: macaulay2_console()                    # not tested
        Macaulay 2, version 1.1
        with packages: Classic, Core, Elimination, IntegralClosure, LLLBases, Parsing, PrimaryDecomposition, SchurRings, TangentCone
        ...

    """
    from sage.repl.rich_output.display_manager import get_display_manager
    if not get_display_manager().is_in_terminal():
        raise RuntimeError('Can use the console only in the terminal. Try %%macaulay2 magics instead.')
    os.system('M2')



def reduce_load_macaulay2():
    """
    Used for reconstructing a copy of the Macaulay2 interpreter from a pickle.

    EXAMPLES::

        sage: from sage.interfaces.macaulay2 import reduce_load_macaulay2
        sage: reduce_load_macaulay2()
        Macaulay2
    """
    return macaulay2

