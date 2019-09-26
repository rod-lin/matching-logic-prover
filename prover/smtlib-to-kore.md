```k
module SMTLIB-TO-KORE
  imports KORE-SUGAR
  imports KORE-HELPERS
  imports PROVER-CONFIGURATION
  imports SMTLIB2
  imports SMTLIB-SL
  imports PROVER-CORE-SYNTAX
  imports PROVER-HORN-CLAUSE-SYNTAX
//  imports STRATEGY

  rule <k> S:SMTLIB2Script
        => \exists { .Patterns } \and( .Patterns ) ~> S
           ...
       </k>

  rule <k> P:Pattern ~> C Cs:SMTLIB2Script
        => P ~> C ~> Cs
           ...
       </k>

  rule <k> \exists { Us } \and(Ps) ~> ((set-logic _) => .) ... </k>
  rule <k> \exists { Us } \and(Ps) ~> ((set-info ATTR _) => .) ... </k>
    requires ATTR =/=K :mlprover-strategy

  rule <k> \exists { Us } \and(Ps) ~> (assert TERM)
        => \exists { Us } \and(SMTLIB2TermToPattern(TERM, Us), Ps)
           ...
       </k>

  rule <k> \exists { Us } \and(Ps) ~> ((declare-sort SORT 0) => .) ... </k>
       <declarations> ( .Bag
                     => <declaration> sort SMTLIB2SortToSort(SORT) </declaration>
                      ) ...
       </declarations>

  rule <k> \exists { Us } \and(Ps) ~> (declare-const ID SORT)
        => \exists { SMTLIB2SimpleSymbolToVariableName(ID) { SMTLIB2SortToSort(SORT) }, Us } \and(Ps)
           ...
       </k>

  rule <k> \exists { Us } \and(Ps) ~> (declare-heap (LOC DATA) .SMTLIB2SortPairList)
        => \exists { Us } \and(Ps)
           ...
       </k>
       <declarations> ( .Bag
                     => <declaration> sort Heap </declaration>
                        <declaration> symbol pto(SMTLIB2SortToSort(LOC), SMTLIB2SortToSort(DATA)) : Heap </declaration>
                        <declaration> symbol sep(Heap, Heap) : Heap </declaration>
                      ) ...
       </declarations>

  rule <k> \exists { Us } \and(Ps) ~> ((declare-datatypes ( .SMTLIB2SortDecList ) ( .SMTLIB2DatatypeDecList )) => .) ... </k>

  rule <k> \exists { Us } \and(Ps) ~> (declare-datatypes ( (SORT1 0) SDECs ) ( ( ( CTOR ( SYM SORT2 ) .SMTLIB2SelectorDecList ) .SMTLIB2ConstructorDecList ) DDECs ) )
        => \exists { Us } \and(Ps) ~> (declare-datatypes ( SDECs ) ( DDECs ))
           ...
       </k>
       <declarations> ( .Bag
                     => <declaration> sort SMTLIB2SortToSort(SORT1) </declaration>
                        <declaration> symbol SMTLIB2SimpleSymbolToSymbol(CTOR)(SMTLIB2SortToSort(SORT2)) : SMTLIB2SortToSort(SORT1) </declaration>
                        <declaration> symbol SMTLIB2SimpleSymbolToSymbol(SYM)(SMTLIB2SortToSort(SORT2)) : SMTLIB2SortToSort(SORT2) </declaration>
                      ) ...
       </declarations>

  rule <k> \exists { Us } \and(Ps) ~> (define-fun-rec ID (ARGS) RET BODY)
        => \exists { Us } \and(Ps)
           ...
       </k>
       <declarations> ( .Bag
                     => <declaration> symbol SMTLIB2SimpleSymbolToSymbol(ID)(SMTLIB2SortedVarListToSorts(ARGS)) : Bool </declaration>
                        <declaration> axiom \forall { SMTLIB2SortedVarListToPatterns(ARGS) }
                                         \iff-lfp( SMTLIB2SimpleSymbolToSymbol(ID)(SMTLIB2SortedVarListToPatterns(ARGS))
                                                 , #normalizeDefinition(SMTLIB2TermToPattern(BODY, SMTLIB2SortedVarListToPatterns(ARGS)))
                                                 )
                        </declaration>
                        <declaration> axiom functional(SMTLIB2SimpleSymbolToSymbol(ID)) </declaration>
                      ) ...
       </declarations>

  rule <k> P:Pattern ~> (check-sat) ~> (set-info :mlprover-strategy S) .SMTLIB2Script
        => claim \not(P) strategy S ~> P
           ...
      </k>

  syntax Pattern ::= #normalizeDefinition(Pattern) [function]
  // rule #normalizeDefinition(\or(Ps)) => \or(#addExistentials(#flattenOrs(#dnfPs(Ps))))
  rule #normalizeDefinition(\or(Ps)) => \or(#addExistentials(#flattenOrs(Ps)))

  syntax Patterns ::= #addExistentials(Patterns) [function]
  rule #addExistentials(.Patterns) => .Patterns
  rule #addExistentials(\and(Ps1), Ps2) => \exists{.Patterns} \and(Ps1), #addExistentials(Ps2)
  rule #addExistentials(\exists{Ps1} P, Ps2) => \exists{Ps1} P, #addExistentials(Ps2)

  syntax Patterns ::= #concatenatePatterns(Patterns, Patterns) [function]
  rule #concatenatePatterns(.Patterns, Ps) => Ps
  rule #concatenatePatterns((P, Ps1), Ps2) => P, #concatenatePatterns(Ps1, Ps2)

  syntax Pattern ::= SMTLIB2TermToPattern(SMTLIB2Term, Patterns) [function]

  rule SMTLIB2TermToPattern( (exists ( ARGS ) T), Vs ) => \exists { SMTLIB2SortedVarListToPatterns(ARGS) } SMTLIB2TermToPattern(T, #concatenatePatterns(SMTLIB2SortedVarListToPatterns(ARGS), Vs))

  rule SMTLIB2TermToPattern((and L R), Vs) => \and(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))
  rule SMTLIB2TermToPattern((or L R), Vs) => \or(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))

  rule SMTLIB2TermToPattern((distinct L R), Vs) => \not(\equals(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs)))

  rule SMTLIB2TermToPattern((= L R), Vs) => \equals(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))
  rule SMTLIB2TermToPattern((> L R), Vs) => gt(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))
  rule SMTLIB2TermToPattern((+ L R), Vs) => plus(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))
  rule SMTLIB2TermToPattern((- L R), Vs) => minus(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))
  rule SMTLIB2TermToPattern((* L R), Vs) => mult(SMTLIB2TermToPattern(L, Vs), SMTLIB2TermToPattern(R, Vs))
  rule SMTLIB2TermToPattern((not P), Vs) => \not(SMTLIB2TermToPattern(P, Vs))
  rule SMTLIB2TermToPattern((ite C L R), Vs) => \or( \and(SMTLIB2TermToPattern(C, Vs), SMTLIB2TermToPattern(L, Vs))
                                                   , \and(\not(SMTLIB2TermToPattern(C, Vs)), SMTLIB2TermToPattern(R, Vs)))
  rule SMTLIB2TermToPattern(I:Int, _) => I
  rule SMTLIB2TermToPattern(true, _) => \top()
  rule SMTLIB2TermToPattern(false, _) => \bottom()
  rule SMTLIB2TermToPattern((as nil _), _) => \bottom()

  rule SMTLIB2TermToPattern((ID Ts), Vs) => SMTLIB2SimpleSymbolToSymbol(ID)(SMTLIB2TermListToPatterns(Ts, Vs))
    [owise]
  rule SMTLIB2TermToPattern(ID:SMTLIB2SimpleSymbol, Vs) => SMTLIB2SimpleSymbolToVariableName(ID) { getSortForVariableName(SMTLIB2SimpleSymbolToVariableName(ID), Vs) }
    [owise]

  syntax Patterns ::= SMTLIB2TermListToPatterns(SMTLIB2TermList, Patterns) [function]
  rule SMTLIB2TermListToPatterns(.SMTLIB2TermList, _) => .Patterns
  rule SMTLIB2TermListToPatterns(T Ts, Vs) => SMTLIB2TermToPattern(T, Vs), SMTLIB2TermListToPatterns(Ts, Vs)

  syntax Patterns ::= SMTLIB2SortedVarListToPatterns(SMTLIB2SortedVarList) [function]
  rule SMTLIB2SortedVarListToPatterns(.SMTLIB2SortedVarList) => .Patterns
  rule SMTLIB2SortedVarListToPatterns((SYMBOL SORT) Ss) => SMTLIB2SimpleSymbolToVariableName(SYMBOL) { SMTLIB2SortToSort(SORT) }, SMTLIB2SortedVarListToPatterns(Ss)

  syntax Sorts ::= SMTLIB2SortedVarListToSorts(SMTLIB2SortedVarList) [function]
  rule SMTLIB2SortedVarListToSorts(.SMTLIB2SortedVarList) => .Sorts
  rule SMTLIB2SortedVarListToSorts((SYMBOL SORT) Ss) => SMTLIB2SortToSort(SORT), SMTLIB2SortedVarListToSorts(Ss)
```

```k
endmodule
```