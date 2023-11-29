:- set_prolog_flag(answer_write_options,[max_depth(0), spacing(next_argument)]).
:- set_prolog_flag(stack_limit, 64 000 000 000).
:- set_prolog_flag(last_call_optimisation, true).

:- dynamic(placedImages/3).
:- dynamic(link/4).
:- dynamic(image/3).
:- dynamic(node/3).

:- dynamic(maxReplicas/1).

%:- table (transferTime/4) as incremental.
%:- dynamic([link/4], [incremental(true)]).
%:- dynamic([image/3], [incremental(true)]).
