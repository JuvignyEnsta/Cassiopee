/*
    Copyright 2013-2024 Onera.

    This file is part of Cassiopee.

    Cassiopee is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Cassiopee is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Cassiopee.  If not, see <http://www.gnu.org/licenses/>.
*/
#define K_ARRAY_UNIQUE_SYMBOL
#include "xcore.h"
#include "SplitElement/splitter.h"
#include "test/xmpi_t1.hpp"

// ============================================================================
/* Dictionnary of all functions of the python module */
// ============================================================================
static PyMethodDef Pyxcore [] =
{
  {"test_all", xcore::test_all, METH_VARARGS}, // all xmpi tests
  {"splitElements", splitElements, METH_VARARGS},
  {"adaptMesh", K_XCORE::adaptMesh, METH_VARARGS},
  {"chunk2partNGon", K_XCORE::chunk2partNGon, METH_VARARGS},
  {"chunk2partElt", K_XCORE::chunk2partElt, METH_VARARGS},
  {"exchangeFields", K_XCORE::exchangeFields, METH_VARARGS},

  {"createAdaptMesh", K_XCORE::createAdaptMesh, METH_VARARGS},
  {"adaptMeshSeq", K_XCORE::adaptMeshSeq, METH_VARARGS},
  {"extractLeafMesh", K_XCORE::extractLeafMesh, METH_VARARGS},
  
  {"adaptMeshDir", K_XCORE::adaptMeshDir, METH_VARARGS},

  {"CreateAdaptMesh", K_XCORE::CreateAdaptMesh, METH_VARARGS},
  {"AdaptMesh", K_XCORE::AdaptMesh, METH_VARARGS},
  {"computeHessian", K_XCORE::computeHessian, METH_VARARGS},
  {"computeGradient", K_XCORE::computeGradient, METH_VARARGS},
  {"hessianToMetric", K_XCORE::hessianToMetric, METH_VARARGS},
  {"_makeRefDataFromGradAndHess", K_XCORE::_makeRefDataFromGradAndHess, METH_VARARGS},
  {"_prepareMeshForAdaptation", K_XCORE::_prepareMeshForAdaptation, METH_VARARGS},
  {"ExtractLeafMesh", K_XCORE::ExtractLeafMesh, METH_VARARGS},
  {"_assignRefDataToAM", K_XCORE::_assignRefDataToAM, METH_VARARGS},
  {"extractBoundaryMesh", K_XCORE::extractBoundaryMesh, METH_VARARGS},

  {"intersectSurf", K_XCORE::intersectSurf, METH_VARARGS},
  {"removeIntersectingKPlanes", K_XCORE::removeIntersectingKPlanes, METH_VARARGS},
  {NULL, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "xcore",
        NULL,
        -1,
        Pyxcore
};
#endif

// ============================================================================
/* Init of module */
// ============================================================================
extern "C"
{
#if PY_MAJOR_VERSION >= 3
  PyMODINIT_FUNC PyInit_xcore();
  PyMODINIT_FUNC PyInit_xcore()
#else
  PyMODINIT_FUNC initxcore();
  PyMODINIT_FUNC initxcore()
#endif
  {
    import_array();
#if PY_MAJOR_VERSION >= 3
    PyObject* module = PyModule_Create(&moduledef);
#else
    Py_InitModule("xcore", Pyxcore);
#endif
#if PY_MAJOR_VERSION >= 3
    return module;
#endif
  }
}
