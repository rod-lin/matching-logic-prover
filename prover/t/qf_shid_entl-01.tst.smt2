(set-logic QF_SHID)

(set-info :source |
  James Brotherston, Nikos Gorogiannis, and Rasmus Petersen
  A Generic Cyclic Theorem Prover. APLAS, 2012.
  https://github.com/ngorogiannis/cyclist
|)
(set-info :smt-lib-version 2.0)
(set-info :category "crafted")
(set-info :status unsat)
(set-info :version "2014-05-31")

(declare-sort RefGTyp 0)

(declare-datatypes (
	(GTyp 0)
	) (
	((c_GTyp (f0 RefGTyp) ))
	)
)

(declare-heap (RefGTyp GTyp) 
)

(define-fun-rec RList ((x RefGTyp)(y RefGTyp)) Bool
	(or 
		(and 
			(distinct (as nil RefGTyp) x)
			(pto x (c_GTyp y ))
		)

		(exists ((xp RefGTyp))
	 
		(and 
			(distinct (as nil RefGTyp) xp)
		(sep 
			(pto xp (c_GTyp y ))
			(RList x xp )
		)

		)

		)

	)
)

(declare-const x RefGTyp)
(declare-const y RefGTyp)
(declare-const z RefGTyp)

(assert 
		(sep 
			(pto x (c_GTyp y ))
			(RList y z )
		)

)

(assert (not 
			(RList x z )
))

(check-sat)

