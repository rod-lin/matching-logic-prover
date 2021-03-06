These strategies encompass a variety of simplification strategies

```k
module STRATEGY-SIMPLIFICATION
  imports PROVER-CORE
  imports STRATEGIES-EXPORTED-SYNTAX
  imports KORE-HELPERS
  imports SYNTACTIC-MATCH-SYNTAX
  imports VISITOR-SYNTAX


```

### remove-lhs-existential

```
         phi -> psi
  -----------------------
  (\exists x. phi) -> psi
```

```k
  rule <claim> \implies(LHS => #lhsRemoveExistentials(LHS), RHS) </claim>
       <k> remove-lhs-existential => noop ... </k>

  syntax Pattern  ::= #lhsRemoveExistentials(Pattern)    [function]
  syntax Patterns ::= #lhsRemoveExistentialsPs(Patterns) [function]

  rule #lhsRemoveExistentialsPs(.Patterns) => .Patterns
  rule #lhsRemoveExistentialsPs(P, Ps)
    => #lhsRemoveExistentials(P), #lhsRemoveExistentialsPs(Ps)

  rule #lhsRemoveExistentials(N:Int) => N
  rule #lhsRemoveExistentials(X:Variable) => X
  rule #lhsRemoveExistentials(S:Symbol) => S
  rule #lhsRemoveExistentials(S:Symbol(ARGS) ) => S(#lhsRemoveExistentialsPs(ARGS))

  rule #lhsRemoveExistentials(\top()) => \top()
  rule #lhsRemoveExistentials(\bottom()) => \bottom()
  rule #lhsRemoveExistentials(\equals(P1, P2))
    => \equals(#lhsRemoveExistentials(P1), #lhsRemoveExistentials(P2))
  rule #lhsRemoveExistentials(\not(P)) => \not(P)

  rule #lhsRemoveExistentials(\implies(LHS, RHS))
    => \implies(#lhsRemoveExistentials(LHS), #lhsRemoveExistentials(RHS))
  rule #lhsRemoveExistentials(\and(Ps)) => \and(#lhsRemoveExistentialsPs(Ps))
  rule #lhsRemoveExistentials(\or(Ps)) => \or(#lhsRemoveExistentialsPs(Ps))
  rule #lhsRemoveExistentials(\forall { U } P) => \forall { U } #lhsRemoveExistentials(P)
  rule #lhsRemoveExistentials(\exists { E } P) => #lhsRemoveExistentials(P)

// It is sound to be conservative. This is needed for implicationContext
  rule #lhsRemoveExistentials(P) => P [owise]
```

Normalize:

 - convert claim to implication
 - RHS has existential qunatifier
 - Implications on the LHS of the goal are always universally quantified.
 - All \ands are flattened

```k

  rule <claim> P::Pattern => \and(P) </claim>
       <k> normalize ... </k>
       requires \and(...) :/=K P andBool \implies(...) :/=K P

  rule <claim> \and(P) => \implies(\and(.Patterns), \and(P)) </claim>
       <k> normalize ... </k>

  rule <claim> \implies(LHS, \and(RHS))
        => \implies(LHS, \exists { .Patterns } \and(RHS))
       </claim>
       <k> normalize ... </k>

  rule <claim> \implies(\and(LHS), \exists { Es } \and(RHS))
        => \implies( \and(#normalizePs(#flattenAnds(#lhsRemoveExistentialsPs(LHS))))
                   , \exists { Es } \and(#normalizePs(#flattenAnds(RHS)))
                   )
       </claim>
       <k> normalize => noop ... </k>

  rule <claim> \not(_) #as P => #normalize(P) </claim>
       <k> normalize => noop ... </k>

  syntax Pattern ::= #normalize(Pattern) [function]
  syntax Patterns ::= #normalizePs(Patterns) [function]

  rule #normalizePs(.Patterns) => .Patterns
  rule #normalizePs(P, Ps) => #normalize(P), #normalizePs(Ps)

  // TODO: normalize on LHS and RHS?
  rule #normalize(\implies(LHS, RHS))
    => \forall { .Patterns } \implies(LHS, RHS)
  rule #normalize(\exists{.Patterns} P)
    => #normalize(P)

  rule #normalize(\not(\exists{Vs} P)) => \forall{Vs} #normalize(\not(P))
  rule #normalize(\not(\and(Ps))) => #normalize(\or(#not(Ps)))
  rule #normalize(\not(\not(P))) => #normalize(P)
  rule #normalize(\or(Ps)) => \or(#normalizePs(Ps))
  rule #normalize(P) => P
    [owise]
```

### purify

LHS terms of the form S(T, Vs) become S(V, Vs) /\ V = T

```k
  rule <claim> \implies(LHS => #purify(LHS), RHS) </claim>
       <k> purify => noop ... </k>

  syntax Pattern ::= #purify(Pattern) [function]
  syntax Patterns ::= #purifyPs(Patterns) [function]
  rule #purify(S(ARGs))
    => #fun( VARs
          => \and( S(VARs), #makeEqualities(VARs, ARGs) )
           )( makePureVariables(ARGs) )
    requires isUnfoldable(S)
  rule #purify(\and(Ps)) => \and(#purifyPs(Ps))
  rule #purify(symbol(sep)(Ps)) => symbol(sep)(#purifyPs(Ps))
  rule #purify(\not(P)) => \not(#purify(P))
  rule #purify(\equals(P1, P2)) => \equals(P1, P2)
  rule #purify(S:Symbol(Ps)) => S(Ps)
    [owise]
  rule #purifyPs(.Patterns) => .Patterns
  rule #purifyPs(P, Ps) => #purify(P), #purifyPs(Ps)

  syntax Patterns ::= makePureVariables(Patterns) [function]
  rule makePureVariables(V:Variable, REST) => V, makePureVariables(REST)
  rule makePureVariables(P, REST) => !V1:VariableName { getReturnSort(P) }, makePureVariables(REST)
    requires notBool isVariable(P)
  rule makePureVariables(.Patterns) => .Patterns

  syntax Patterns ::= #getNonVariables(Patterns) [function]
  rule #getNonVariables(.Patterns) => .Patterns
  rule #getNonVariables(V:Variable, Ps) => #getNonVariables(Ps)
  rule #getNonVariables(P, Ps) => P, #getNonVariables(Ps)
    requires notBool isVariable(P)

  syntax Patterns ::= #makeEqualities(Patterns, Patterns) [function]
  rule #makeEqualities(.Patterns, .Patterns) => .Patterns
  rule #makeEqualities((V, Vs), (V, Ps)) => #makeEqualities(Vs, Ps)
  rule #makeEqualities((V, Vs), (P, Ps)) => \equals(V, P), #makeEqualities(Vs, Ps)
    requires V =/=K P
```

### abstraction

obligation of the form R(T, Vs) => R(T', Vs') becomes
R(V, Vs) => exists V', R(V', Vs') and V = V'

```k
  rule <claim> \implies(LHS, RHS) </claim>
       <k> abstract
               => #getNewVariables(LHS, .Patterns)
               ~> #getNewVariables(RHS, .Patterns)
               ~> abstract
              ...
       </k>

  rule <claim> \implies(LHS, \and(\or(RHS)))
            => \implies( #abstract(LHS, VsLHS)
                       , \exists{ VsRHS } \and( #dnf(\or(\and(#createEqualities(VsLHS, VsRHS))))
                                                , #abstract(RHS, VsRHS)
                                                )
                       )
       </claim>
       <k> (VsLHS:Patterns ~> VsRHS:Patterns ~> abstract) => noop ... </k>

  syntax Patterns ::= #getNewVariables(Pattern, Patterns) [function]
  syntax Patterns ::= #getNewVariablesPs(Patterns, Patterns) [function]
  rule #getNewVariables(\and(Ps), Vs) => #getNewVariablesPs(Ps, Vs)
  rule #getNewVariables(\or(Ps), Vs) => #getNewVariablesPs(Ps, Vs)
  rule #getNewVariables(\not(P), Vs) => #getNewVariablesPs(P, Vs)
  rule #getNewVariables(symbol(sep)(Ps), Vs) => #getNewVariablesPs(Ps, Vs)
  rule #getNewVariables(S(ARGs), Ps)
    => (makePureVariables(ARGs) -Patterns ARGs) ++Patterns Ps
    requires isUnfoldable(S)
  rule #getNewVariables(symbol(pto)(_), Ps) => Ps
  rule #getNewVariables(\equals(_, _), Ps) => Ps

  rule #getNewVariablesPs(.Patterns, _) => .Patterns
  rule #getNewVariablesPs((P, Ps), Vs) => #getNewVariables(P, Vs) ++Patterns #getNewVariablesPs(Ps, Vs)

  syntax Pattern ::= #abstract(Pattern, Patterns) [function]
  syntax Patterns ::= #abstractPs(Patterns, Patterns) [function]
  rule #abstract(\and(Ps), Vs) => \and(#abstractPs(Ps, Vs))
  rule #abstract(\or(Ps), Vs) => \or(#abstractPs(Ps, Vs))
  rule #abstract(\not(P), Vs) => \not(#abstract(P, Vs))
  rule #abstract(symbol(sep)(Ps), Vs) => symbol(sep)(#abstractPs(Ps, Vs))
  rule #abstract(S(ARGs), Vs)
    => S(#replaceNewVariables(ARGs, Vs))
    requires isUnfoldable(S)
  rule #abstract(symbol(pto)(ARGs), Vs) => symbol(pto)(ARGs)
  rule #abstract(\equals(L, R), Vs) => \equals(L, R)

  rule #abstractPs(.Patterns, _) => .Patterns
  rule #abstractPs((P, Ps), Vs) => #abstract(P, Vs), #abstractPs(Ps, Vs)

  syntax Patterns ::= #replaceNewVariables(Patterns, Patterns) [function]
  rule #replaceNewVariables((V1:Variable, Ps), Vs) => V1, #replaceNewVariables(Ps, Vs)
  rule #replaceNewVariables((P, Ps), (V, Vs)) => V, #replaceNewVariables(Ps, Vs)
    requires notBool isVariable(P)
  rule #replaceNewVariables(.Patterns, _) => .Patterns

  syntax Patterns ::= #createEqualities(Patterns, Patterns) [function]
  syntax Patterns ::= #createEqualitiesVar(Patterns, Pattern) [function]
  rule #createEqualities(VsLHS, .Patterns) => .Patterns
  rule #createEqualities(VsLHS, (VRHS, VsRHS)) => \or(#createEqualitiesVar(VsLHS, VRHS)), #createEqualities(VsLHS, VsRHS)
  rule #createEqualitiesVar(.Patterns, VRHS) => .Patterns
  rule #createEqualitiesVar((VLHS, VsLHS), VRHS) => \equals(VRHS, VLHS), #createEqualitiesVar(VsLHS, VRHS)
```

### lift-constraints

Bring predicate constraints to the top of a term.

```k
  rule <claim> \implies(\and(Ps) => #flattenAnd(#liftConstraints(\and(Ps)))
                       , \exists { _ } (\and(Rs) => #flattenAnd(#liftConstraints(\and(Rs))))
                       )
       </claim>
       <k> lift-constraints => noop ... </k>

  syntax Pattern ::= #liftConstraints(Pattern) [function]
  rule #liftConstraints(P) =>     P  requires isPredicatePattern(P)
  rule #liftConstraints(S) => symbol(sep)(S) requires isSpatialPattern(S)

  rule #liftConstraints(symbol(sep)(\and(.Patterns), REST)) => #liftConstraints(symbol(sep)(REST))

  rule #liftConstraints(symbol(sep)(\and(P, Ps:Patterns), REST:Patterns))
    => #liftConstraints(\and(symbol(sep)(\and(Ps), REST), P, .Patterns))
    requires isPredicatePattern(P)
  rule #liftConstraints(symbol(sep)(\and(P, Ps), REST))
    => #liftConstraints(symbol(sep)(\and(Ps), P, REST))
    requires isSpatialPattern(P)
  rule #liftConstraints(symbol(sep)(\and(P, Ps), REST))
    => #liftConstraints(symbol(sep)(\and(#flattenAnds(#liftConstraints(P), Ps)), REST))
    requires notBool isPredicatePattern(P) andBool notBool isSpatialPattern(P)

  // Rotate
  rule #liftConstraints(symbol(sep)(S, Ps))
    => #liftConstraints(symbol(sep)(Ps ++Patterns S))
    requires isSpatialPattern(S) andBool notBool isSpatialPattern(symbol(sep)(S, Ps))

  rule #liftConstraints(\and(symbol(sep)(Ss), Ps))
    => #liftConstraints(\and(#flattenAnds(#liftConstraints(symbol(sep)(Ss)), .Patterns) ++Patterns Ps))
    requires notBool isSpatialPattern(symbol(sep)(Ss))

  rule #liftConstraints(\and(S, Ps))
    => \and(symbol(sep)(S), #flattenAnds(#liftConstraints(\and(Ps)), .Patterns))
    requires isSpatialPattern(S)

  rule #liftConstraints(\and(\and(Ps), REST))
    => #liftConstraints(\and(Ps ++Patterns REST))

  rule #liftConstraints(\and(P, Ps))
    => #liftConstraints(\and(Ps ++Patterns P))
  requires isPredicatePattern(P) andBool notBool isPredicatePattern(\and(P, Ps))
```

### lift-or

Lift `\or`s on the left hand sides of implications

```
  (A -> RHS) /\ (B -> RHS)
  ------------------------
        A \/ B -> RHS
```

```k
  rule <claim> \implies(\or(LHSs), RHS) => \and( #liftOr(LHSs, RHS)) </claim>
       <k> lift-or => noop ... </k>

  syntax Patterns ::= "#liftOr" "(" Patterns "," Pattern ")" [function]
  rule #liftOr(.Patterns, RHS) => .Patterns
  rule #liftOr((LHS, LHSs), RHS) => \implies(LHS, RHS), #liftOr(LHSs, RHS)
```

### Simplify

>              phi(x, y) -> psi(y)
> -----------------------------------------
> (\forall .Patterns . phi(x, y)) -> psi(y)

```k
  rule <claim> \implies(\forall { .Patterns } \and(LHS) => \and(LHS), RHS) </claim>
       <k> simplify ... </k>
```

>       phi(x, y) -> psi(y)
> -------------------------------
> \exists X . phi(x, y) -> psi(y)

```k
  rule <claim> \implies(\exists { _ } \and(LHS) => \and(LHS), RHS) </claim>
       <k> simplify ... </k>
```

>    LHS /\ phi -> RHS
> ------------------------
> LHS /\ phi -> RHS /\ phi

```k
  rule <claim> \implies(\and(LHS), \exists { _ } \and(RHS => RHS -Patterns LHS)) </claim>
       <k> simplify => noop ... </k>
```

#### Simplify ands

```k

  rule <k> simplify.flatten-ands => noop ...</k>
       <claim> P => visitorResult.getPattern(visitTopDown(flattenAndsVisitor(), P)) </claim>

  syntax Visitor ::= flattenAndsVisitor()

  rule visit(flattenAndsVisitor(), P)
    => visitorResult(flattenAndsVisitor(), P)
    requires \and(...) :/=K P

  rule visit(flattenAndsVisitor(), \and(Ps))
    => visitorResult(flattenAndsVisitor(), maybeAnd(#flattenAnds(Ps)))

```

### Instantiate Existials

```
           phi /\ x = t -> psi
     -------------------------------
     phi -> \exists x . x = t /\ psi
```

```k
  rule <claim> \implies( \and(LHS) , \exists { EXIST } \and(RHS) ) #as GOAL </claim>
       <k> (. => getAtomForcingInstantiation(RHS, getExistentialVariables(GOAL)))
               ~> instantiate-existentials
                  ...
       </k>

  rule <claim> \implies( \and(LHS) , \exists { EXIST } \and(RHS) )
            => \implies( \and(LHS ++Patterns INSTANTIATION)
                       , \exists { EXIST -Patterns getFreeVariables(INSTANTIATION) }
                         \and(RHS -Patterns INSTANTIATION)
                       )
       </claim>
       <k> (INSTANTIATION => .) ~> instantiate-existentials ... </k>
     requires INSTANTIATION =/=K .Patterns

  rule <k> (.Patterns ~> instantiate-existentials) => noop ... </k>

  syntax Patterns ::= getAtomForcingInstantiation(Patterns, Patterns) [function]
  rule getAtomForcingInstantiation((\equals(X:Variable, P), Ps), EXISTENTIALS)
    => \equals(X:Variable, P), .Patterns
    requires X in EXISTENTIALS
     andBool getFreeVariables(P, .Patterns) intersect EXISTENTIALS ==K .Patterns
  rule getAtomForcingInstantiation((\equals(P, X:Variable), Ps), EXISTENTIALS)
    => \equals(X:Variable, P), .Patterns
    requires X in EXISTENTIALS
     andBool getFreeVariables(P, .Patterns) intersect EXISTENTIALS ==K .Patterns
  rule getAtomForcingInstantiation((P, Ps), EXISTENTIALS)
    => getAtomForcingInstantiation(Ps, EXISTENTIALS) [owise]
  rule getAtomForcingInstantiation(.Patterns, EXISTENTIALS)
    => .Patterns
```

### Substitute Equals for equals

```
     PHI[x/y] -> PSI[x/y]
    ----------------------  where y is a variable
     x = y /\ PHI -> PSI
```

```k
  rule <claim> \implies(\and(LHS), _) </claim>
       <k> substitute-equals-for-equals
               => (makeEqualitySubstitution(LHS) ~> substitute-equals-for-equals)
                  ...
       </k>

  rule <k> (SUBST:Map ~> substitute-equals-for-equals)
               => noop
                  ...
       </k>
    requires SUBST ==K .Map

  rule <claim> \implies( \and(LHS => removeTrivialEqualities(substPatternsMap(LHS, SUBST)))
                       , \exists { _ }
                         ( \and(RHS => removeTrivialEqualities(substPatternsMap(RHS, SUBST))) )
                       )
       </claim>
       <k> (SUBST:Map ~> substitute-equals-for-equals)
               => substitute-equals-for-equals
                  ...
       </k>
    requires SUBST =/=K .Map

  syntax Map ::= makeEqualitySubstitution(Patterns) [function]
  rule makeEqualitySubstitution(.Patterns) => .Map
  rule makeEqualitySubstitution(\equals(X:Variable, T), Ps) => (X |-> T) .Map
  rule makeEqualitySubstitution(\equals(T, X:Variable), Ps) => (X |-> T) .Map
    requires notBool(isVariable(T))
  rule makeEqualitySubstitution((P, Ps:Patterns)) => makeEqualitySubstitution(Ps) [owise]

  syntax Patterns ::= removeTrivialEqualities(Patterns) [function]
  rule removeTrivialEqualities(.Patterns) => .Patterns
  rule removeTrivialEqualities(\equals(X, X), Ps) => removeTrivialEqualities(Ps)
  rule removeTrivialEqualities(P, Ps) => P, removeTrivialEqualities(Ps) [owise]
```


### Universal generalization

```
     P(x)
    ----------------------
    \forall x. P(x)
```

```k

  rule <claim> \forall{_} P => P </claim>
       <k> universal-generalization => noop ...</k>

```

### Propagate exists

The strategy `propagate-exists-through-application N` finds the Nth existential
quantifier that is used as an argument of an application, and propagates it outside
the application. For example, the formula `f(\exists X. Phi)` gets rewritten
to `\exists X. f(Phi)`.

```
Gamma |- C[\exists X. C_\sigma[Phi]]
------------------------------------
Gamma |- C[C_\sigma[\exists X. Phi]]
```

```k
  rule <claim> P
            => propagateExistsThroughApplicationVisitorResult(
                 visitTopDown(
                   propagateExistsThroughApplicationVisitor(N),
                   P
                 )
               )
      </claim>
       <k> propagate-exists-through-application N
               => noop
       ...</k>

  syntax Visitor ::= propagateExistsThroughApplicationVisitor(Int)

  syntax Pattern ::= propagateExistsThroughApplicationVisitorResult(VisitorResult) [function]

  rule propagateExistsThroughApplicationVisitorResult(visitorResult(_, P)) => P

  rule visit(propagateExistsThroughApplicationVisitor(N) #as V, P)
       => #if isApplication(P) andBool N >=Int 0
          #then propagateExistsThroughApplication(N, P)
          #else visitorResult(V, P) #fi

  syntax VisitorResult ::= propagateExistsThroughApplication(Int, Pattern) [function]
                         | #propagateExistsThroughApplication(Patterns, Int, Symbol, Patterns) [function]

  rule propagateExistsThroughApplication(N, S::Symbol(Ps::Patterns))
    => #propagateExistsThroughApplication(.Patterns, N, S, Ps)

  rule #propagateExistsThroughApplication(Ps1, N, S, (P, Ps2))
    => #propagateExistsThroughApplication((Ps1 ++Patterns P, .Patterns), N, S, Ps2)
    requires ((\exists{_} _) :/=K P) orBool ((\exists{.Patterns} _) :=K P)

  rule #propagateExistsThroughApplication(Ps1, N, S, (\exists{V, Vs} P, Ps2))
    => #propagateExistsThroughApplication(Ps1 ++Patterns (\exists{V, Vs} P, .Patterns), N -Int 1, S, Ps2)
    requires N >=Int 1

  rule #propagateExistsThroughApplication(Ps1, 0, S, (\exists{V, Vs} P, Ps2))
    => visitorResult(
         propagateExistsThroughApplicationVisitor(-1),
         \exists{V} (S(Ps1 ++Patterns (maybeExists{Vs} P, .Patterns) ++Patterns Ps2))
       )

  rule #propagateExistsThroughApplication(Ps, N, S, .Patterns)
    => visitorResult(
         propagateExistsThroughApplicationVisitor(N),
         S(Ps)
       )

```

### Propagate predicate

`propagate-predicate-through-application(P, N)` rewrites a subpattern of the form
`f(Pred /\ Phi)` to `Pred /\ f(Phi)`, given that `Pred` is a predicate.
The subpattern is chosen such that `Pred` is the `N`th (counting from 0) instance of the pattern `P`
that is immediately surrounded by `\and(...)` and symbol application.
For instance, if N=3 and P=\equals(#A, #B), then the formula
`f(A=B /\ Phi1, C=D) \/ f(Phi2 /\ E=F, G=H)` gets rewritten to
`f(A=B /\ Phi1, C=D) \/ (E=F /\ f(Phi2, G=H))` (assuming that Phi1 and Phi2 are not equalities).

```

Gamma |- C[P /\ C_\sigma[Phi]]
------------------------------ where P is a predicate pattern
Gamma |- C[C_\sigma[P /\ Phi]]
```

```k
  rule <claim> T
            => pptaVisitorResult(
                 visitTopDown(
                   pptaVisitor(P, N),
                   T
                 )
               )
      </claim>
       <k> propagate-predicate-through-application(P, N)
               => noop
       ...</k>


  syntax Visitor ::= pptaVisitor(Pattern, Int)

  syntax Pattern ::= pptaVisitorResult(VisitorResult) [function]

  rule pptaVisitorResult(visitorResult(_, P)) => P

  rule visit(pptaVisitor(P, N) #as V, T)
       => #if isApplication(T) andBool N >=Int 0
          #then ppta(P, N, T)
          #else visitorResult(V, T) #fi

  syntax VisitorResult ::= ppta(Pattern, Int, Pattern) [function]
                         | "#ppta1" "(" "processedArgs:" Patterns
                                    "," "pattern:" Pattern
                                    "," "index:" Int
                                    "," "symbol:" Symbol
                                    "," "remainingArgs:" Patterns
                                    ")" [function]
                         | "#ppta2" "(" "processedArgs:" Patterns
                                    "," "result:" KItem
                                    "," "currArg:" Pattern
                                    "," "pattern:" Pattern
                                    "," "symbol:" Symbol
                                    "," "remainingArgs:" Patterns
                                    ")" [function]


  rule ppta(P, N, S::Symbol(As::Patterns))
    => #ppta1( processedArgs: .Patterns
             , pattern: P
             , index: N
             , symbol: S
             , remainingArgs: As
             )

  rule #ppta1( processedArgs: As1
             , pattern: P
             , index: N
             , symbol: S
             , remainingArgs: .Patterns
             )
       => visitorResult(pptaVisitor(P, N), S(As1))

  rule #ppta1( processedArgs: As1
             , pattern: P
             , index: N
             , symbol: S
             , remainingArgs: (A, As2)
             )
    => #ppta2( processedArgs: As1
             , result: pptaProcessArg(N, P, A)
             , currArg: A
             , pattern: P
             , symbol: S
             , remainingArgs: As2
             )

  rule #ppta2( processedArgs: As1
             , result: pptaNoMatch(N)
             , currArg: A
             , pattern: P
             , symbol: S
             , remainingArgs: As2
             )
    => #ppta1( processedArgs: As1 ++Patterns (A, .Patterns)
             , pattern: P
             , index: N
             , symbol: S
             , remainingArgs: As2
             )

  rule #ppta2( processedArgs: As1
             , result: pptaMatch(pred: P', newArg: A')
             , currArg: _
             , pattern: P
             , symbol: S
             , remainingArgs: As2
             )
    => visitorResult(
         pptaVisitor(P, -1),
         \and(P', S(As1 ++Patterns (A', .Patterns) ++Patterns As2))
       )

  syntax KItem ::= pptaNoMatch(Int)
                 | "pptaMatch" "(" "pred:" Pattern "," "newArg:" Pattern ")"
                 | pptaProcessArg(Int, Pattern, Pattern) [function]
                 | #pptaProcessArg(Int, Pattern, Patterns, Patterns) [function]

  rule pptaProcessArg(N, P, T)
    => pptaNoMatch(N)
       requires \and(_) :/=K T

  rule pptaProcessArg(N, P, \and(Ps))
    => #pptaProcessArg(N, P, .Patterns, Ps)

  rule #pptaProcessArg(N, P, Ps1, .Patterns)
    => pptaNoMatch(N)

  rule #pptaProcessArg(N, P, Ps1, (P', Ps2))
    => #if #matchResult(subst: _) :=K syntacticMatch(
                           terms: (P', .Patterns)
                         , patterns: (P, .Patterns)
                         , variables: getUniversallyQuantifiedVariables(P)
                                      ++Patterns getSetVariables(P)
                         )
          andBool isPredicatePattern(P')
       #then
         #if N ==Int 0 #then
           pptaMatch(pred: P', newArg: maybeAnd(Ps1 ++Patterns Ps2))
         #else
           #pptaProcessArg(N -Int 1, P, Ps1 ++Patterns (P', .Patterns), Ps2)
         #fi
       #else
         #pptaProcessArg(N, P, Ps1 ++Patterns (P', .Patterns), Ps2)
       #fi

```
### Propagate conjunct through exists

In its simplest form, `propagate-conjunct-through-exists(0,0)`
rewrites the pattern `\exists X. (Pi /\ Psi)` to `Pi /\ exists X. Psi`,
assuming that `Pi` does not contain free `X`. In the general form,
`propagate-conjunct-through-exists(N, M)` will operate on the M-th conjunct
of the N-th instance of the pattern `\exists {_} \and(...)`.

```
Gamma |- C[Pi /\ \exists X. Psi]
-------------------------------- where X not free in Pi
Gamma |- C[\exists X. Pi /\ Psi]
```

```k

  rule <claim> T
            => visitorResult.getPattern(
                 visitTopDown(
                   pcteVisitor(N, M),
                   T
                 )
               )
       </claim>
       <k>
         propagate-conjunct-through-exists(N, M) => noop
       ...</k>

  syntax Visitor ::= pcteVisitor(Int, Int)

  rule visit(pcteVisitor(_,_) #as V, P)
    => visitorResult(V, P)
    requires \exists{_} _ :/=K P

  rule visit(pcteVisitor(_,_) #as V, (\exists{_} P') #as P)
    => visitorResult(V, P)
    requires \and(_) :/=K P'

  rule visit(pcteVisitor(N, M) #as V, (\exists{Vs} \and(Ps)) #as P)
    => #if N <Int 0 #then
         visitorResult(V, P)
       #else #if N >Int 0 #then
         visitorResult(pcteVisitor(N -Int 1, M), P)
       #else // N ==Int 0
         pcte1(M, Vs, Ps)
       #fi #fi

  syntax VisitorResult ::= pcte1(Int, Patterns, Patterns) [function]

  rule pcte1(M, Vs, Ps)
    => pcte2(idx: M,
             vars: Vs,
             ps1: takeFirst(M, Ps),
             pattern: getMember(M, Ps),
             ps2: skipFirst(M +Int 1, Ps) )
    requires getLength(Ps) >Int M

  syntax VisitorResult ::= "pcte2" "(" "idx:" Int
                                   "," "vars:" Patterns
                                   "," "ps1:" Patterns
                                   "," "pattern:" Pattern
                                   "," "ps2:" Patterns
                                   ")" [function]

  rule pcte2(idx: M, vars: Vs, ps1: Ps1, pattern: P, ps2: Ps2)
    => visitorResult(
         pcteVisitor(-1, M),
         maybeExists{takeFirst(getLength(Vs) -Int 1, Vs)}
         \and(P, \exists{getLast(Vs), .Patterns} maybeAnd(Ps1 ++Patterns Ps2), .Patterns)
       )
    requires notBool (getLast(Vs) in getFreeVariables(P))

```

```k
endmodule
```

