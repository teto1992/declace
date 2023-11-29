:- consult('config.pl').

placement(Placement, Cost) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(MaxR),
    once(placement(Images, Nodes, MaxR, [], Placement, Cost)).

% Sorts images by size in descending order
imagesToPlace(Images) :-
    findall((S,I), image(I,S,_), X),
    sort(0, @>=, X, SortedImagesDescending),
    findall(I, member((S,I), SortedImagesDescending), Images).

% Sorts candidates by cost in ascending order and by hardware in descending orders
networkNodes(Nodes) :- 
    findall(cand(N,S,C), node(N,S,C), Tmp0),
    findall(cand(N,S,C,Deg), (member(cand(N,S,C), Tmp0), degree(N,Deg)), Tmp),
    % per costo crescente   per banda media decrescente per storage decrescente
    sort(4, @>=, Tmp, Tmp1), sort(2, @>=, Tmp1, Tmp2), sort(3, @=<, Tmp2, Tmp3), 
    findall(N, member(cand(N,S,C,_), Tmp3), Nodes).


degree(N, Deg) :- 
    findall(B, link(N, _, _, B), Bs),  length(Bs, L), (dif(L,0) -> sum_list(Bs, Sum), Deg is Sum/L; Deg=0).

/* Iterative deepening */
placement([I|Mages], Nodes, MaxR, PartialPlacement, Placement, Cost) :-
    iterativeDeepening([I|Mages], Nodes, PartialPlacement, Placement, 1, MaxR), 
    cost(Placement, Cost).
placement([], _, _, POk, POk, Cost) :-
    cost(POk, Cost). %, allocatedStorage(POk,Alloc).

/* Calls imagePlacement/5 while increasing the number of maximum allowed replicas from M to Max */
iterativeDeepening(Images, Nodes, PartialPlacement, Placement, M, MaxR) :-
    M =< MaxR, 
    imagePlacement(Images, Nodes, PartialPlacement, Placement, M), !. 
iterativeDeepening(Images, Nodes, PartialPlacement, Placement, M, MaxR) :-
    M =< MaxR, NewM is M+1,
    iterativeDeepening(Images, Nodes, PartialPlacement, Placement, NewM, MaxR).
    
/* Places Images one by one */
imagePlacement([I|Is], Nodes, PPlacement, Placement, R) :-
    replicaPlacement(I, Nodes, PPlacement, TmpPPlacement, R), !,
    imagePlacement(Is, Nodes, TmpPPlacement, Placement, R).
imagePlacement([],_,Placement,Placement,_).

/* Places at most M replicas of I onto Nodes, until transferTimesOk/3 holds */
replicaPlacement(I, Nodes, Placement, Placement, _) :- 
    transferTimesOk(I, Nodes, Placement), !.
replicaPlacement(I, Nodes, PPlacement, NewPPlacement, R) :-
    % \+ transferTimesOk(I, Nodes, PPlacement), 
    R > 0, NewR is R - 1,
    image(I, Size, _), member(N, Nodes),
    \+ member(at(I,N), PPlacement),
    storageOk(PPlacement, N, Size),
    replicaPlacement(I, Nodes, [at(I, N)|PPlacement], NewPPlacement, NewR).

transferTimesOk(I, [N|Ns], P) :-
    dif(P,[]), member(at(I,M),P),
    image(I,_,MaxR), 
    transferTime(I,M,N,T), T < MaxR, !, % one source is enough
    transferTimesOk(I, Ns, P).
transferTimesOk(_, [], _).

transferTime(Image, Src, Dest, T) :-
    dif(Src, Dest), node(Src, _, _), node(Dest, _, _),
    image(Image, Size, _),
    link(Src, Dest, Latency, Bandwidth),
    T is Size * 8 / Bandwidth + Latency / 1000.
transferTime(_, N, N, 0).

storageOk(I, Size, Placement, Alloc) :-
    findall(N, member(at(I,N), Placement), Nodes), 
    checkStorage(I, Size, Nodes, Placement, Alloc).

checkStorage(I, Size, [N|Ns], Placement, Alloc) :-
    storageOk(Placement, N, Size), checkStorage(I, Size, Ns, Placement, Alloc).
checkStorage(_, _, [], _, _). 

storageOk(Placement, N, Size) :- 
    node(N, Storage, _),
    usedHw(Placement, N, UsedHw),
    Storage - UsedHw >= Size.

cost(Placement, Cost) :- findall(CS, (member(at(I,N),Placement), image(I,S,_), node(N,_,C), CS is C*S), CSs), sum_list(CSs, Cost).

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).

%%% Utils %%%
loadFile(Filename, ToRetract) :-
    open(Filename, read, Str),
	maplist(retractall,ToRetract),
    readAndAssert(Str). 

readAndAssert(Str) :-
    read(Str, X), (X == end_of_file -> close(Str) ; assert(X), readAndAssert(Str)).