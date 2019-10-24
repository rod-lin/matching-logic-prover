Configuration
=============

The configuration consists of a assoc-commutative bag of goals. Only goals
marked `<active>` are executed to control the non-determinism in the system. The
`<claim>` cell contains the Matching Logic Pattern for which we are searching for a
proof. The `<strategy>` cell contains an imperative language that controls which
(high-level) proof rules are used to complete the goal. The `<trace>` cell
stores a log of the strategies used in the search of a proof and other debug
information. Eventually, this could be used for constructing a proof object.

```k
module PROVER-CONFIGURATION
  imports KORE-SUGAR
  imports DOMAINS-SYNTAX

  syntax Pgm
  syntax Strategy

  syntax GoalId ::= "root" | Int

  configuration
      <prover>
        <k> $PGM:Pgm </k>
        <goals>
          <goal multiplicity="*" type="Set" format="%1%i%n%2, %3, %4%n%5%n%6%n%7%n%d%8">
            <active format="active: %2"> true:Bool </active>
            <id format="id: %2"> root </id>
            <parent format="parent: %2"> .K </parent>
            <claim> .K </claim>
            <strategy> .K </strategy>
            <trace> .K </trace>
          </goal>
        </goals>
        <declarations>
          <declaration multiplicity="*" type="Set">  .K </declaration>
        </declarations>
      </prover>
endmodule
```