{
open Parser
}

let digit       = ['0'-'9']
let int         = ['0'] | ['-'] ['1'-'9'] digit* | ['1'-'9'] digit*
let nondigit    = ['a'-'z''A'-'Z''_''$' '+''-''*''/''>''<''=']
let alphabet    = digit | nondigit
let word        = nondigit alphabet*
let space       = [' ' '\t' '\n']

rule token = parse
  | space               { token lexbuf }
  | ';'                 { comment lexbuf }        (* inline comments start with ';' *)
  | '('                 { LPAREN }
  | ')'                 { RPAREN }
  | "declare-sort"      { DECLSORT }
  | "declare-symb"      { DECLSYMB }
  | "declare-func"      { DECLFUNC }
  | "declare-partial"   { DECLPARTIAL }
  | "assert"            { ASSERT }
  | "check-sat"         { CHECKSAT }
  | "get-model"         { GETMODEL }
  | "top"               { TOP }
  | "bottom"            { BOTTOM }
  | "and"               { AND }
  | "or"                { OR }
  | "not"               { NOT }
  | "->"                { IMPLIES }
  | "<->"               { IFF }
  | "="                 { EQUAL }
  | "contains"          { CONTAINS }
  | "forall"            { FORALL }
  | "exists"            { EXISTS }
  | "floor"             { FLOOR }
  | "ceil"              { CEIL }
  | int as n            { INT(int_of_string n) }
  | word as w           { ID(w) }
  | eof                 { EOF }
and comment = parse
  | [^'\n']             { comment lexbuf }        (* ignore anything until seeing a '\n' *)
  | '\n'                { token lexbuf }

  