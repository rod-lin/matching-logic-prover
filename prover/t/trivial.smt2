(assert ( = 1 1 ))
(assert (not ( = 2 2 )))
(check-sat)

(set-info :mlprover-strategy smt)
