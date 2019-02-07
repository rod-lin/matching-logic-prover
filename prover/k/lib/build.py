#!/usr/bin/env python3

from kninja import *
import sys
import os.path

# Project Definition
# ==================

proj = KProject()

build_z3_rule = proj.rule( name        = 'build-z3'
                         , description = 'Building Z3'
                         , command     = 'lib/build-z3 </dev/null "$z3_repo" "$prefix"'
                         ) \
                    .output(proj.builddir('local/bin/z3')) \
                    .variables( pool = 'console'
                              , z3_repo = 'ext/z3'
                              , prefix  = proj.builddir('local/')
                              )
z3_target = proj.source('').then(build_z3_rule)

# Helpers for running tests
# -------------------------

def do_test(defn, file):
    expected = file + '.expected'
    return proj.source(file) \
               .then(defn.krun()) \
               .then(proj.check(proj.source(expected))
                            .variables(flags = '--ignore-all-space')) \
               .alias(file + '.test')

def do_prove(alias, defn, spec_module, spec):
    return proj.source(spec) \
               .then(proj.tangle().ext('spec.k')) \
               .then(defn.kprove().variables(flags = '--spec-module ' + spec_module)) \
               .then(proj.check(proj.source('t/kprove.expected'))) \
               .alias(alias)

# Matching Logic Prover
# =====================

imported_k_files = [ proj.source('kore.md').then(proj.tangle().output(proj.tangleddir('kore.k')))
                   , proj.source('smtlib2.md').then(proj.tangle().output(proj.tangleddir('smtlib2.k')))
                   , proj.source('direct-proof.md').then(proj.tangle().output(proj.tangleddir('direct-proof.k')))
                   ]
prover_k = proj.source('matching-logic-prover.md') \
               .then(proj.tangle().output(proj.tangleddir('matching-logic-prover.k')))
mlprover = prover_k \
            .then(proj.kompile(backend = 'java')
                      .variables(directory = proj.builddir('matching-logic-prover'))
                      .implicit(imported_k_files + [z3_target])
                 )

do_test(mlprover, 't/emptyset-implies-isempty.prover').default()

# List tests
do_test(mlprover, 't/lsegleft-implies-lsegright.prover').default()
do_test(mlprover, 't/lsegleft-implies-list.prover').default()
do_test(mlprover, 't/sortedlist-implies-list.prover').default()
do_test(mlprover, 't/listSortedLength-implies-listLength.prover').default()
do_test(mlprover, 't/lsegleftsorted-sortedlist-implies-sortedlist.prover').default()
do_test(mlprover, 't/listSegmentRightLength-listSegmentRightLength-implies-listSegmentRightLength.prover').default()
do_test(mlprover, 't/listSegmentRightLength-appendone-implies-listSegmentRightLength.prover').default()
do_test(mlprover, 't/lsegright-implies-lsegleft.prover').default()
do_test(mlprover, 't/lsegright-list-implies-list.prover').default()

do_test(mlprover, 't/dllSegmentLeft-dll-implies-dll.prover').default()
do_test(mlprover, 't/dllSegmentLeftLength-dllLength-implies-dllLength.prover').default()
do_test(mlprover, 't/dllSegmentRightLength-dllSegmentRightLength-implies-dllSegmentRightLength.prover').default()

do_test(mlprover, 't/bst-implies-bt.prover').default()
do_test(mlprover, 't/avl-implies-bst.prover').default()

do_test(mlprover, 't/find-before-loop.prover').default()
do_test(mlprover, 't/find-in-loop.prover').default()

do_test(mlprover, 't/LTL-Ind.prover').default()

do_test(mlprover, 't/sum-to-n.prover').default()

do_test(mlprover, 't/zip-zeros-ones-implies-alters.prover').default()

# Failing tests: These tests aren't passing yet. To mark as passing append `.default()`
# and move to above section.
do_test(mlprover, 't/find-after-loop1.prover')
do_test(mlprover, 't/find-after-loop2.prover')

# Theories
# --------

lists = proj.source('lists.md') \
            .then(proj.tangle().output(proj.tangleddir('lists.k'))) \
            .then(proj.kompile(backend = 'kore')
                      .variables(directory = proj.builddir('lists'))
                 ) \
            .alias('lists')

# SMTLIB Translation
# ==================

smtlib_testdriver = prover_k.then(proj.kompile(backend = 'java')
                                      .variables(directory = proj.builddir('smt-testdriver')
                                                 , flags = "--main-module SMTLIB2-TEST-DRIVER --syntax-module SMTLIB2-TEST-DRIVER") 
                                      .implicit(imported_k_files + [z3_target])
                                 )

do_prove('unit-tests', smtlib_testdriver, 'UNIT-TESTS-SPEC', 'unit-tests.md').default()
do_test(smtlib_testdriver, 't/test.smt').alias('smt-test')
