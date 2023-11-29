:- consult('config.pl').

declace(Placement, Cost) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(MaxR),
    once(crPlacement(Images, Nodes, MaxR, Placement, Cost)).

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
    
% Determines a Placement of Images onto Nodes, possibly "repairing" an initial Placement
crPlacement(Images, Nodes, MaxR, NewPlacement, Cost) :- 
    placedImages(Placement, Alloc, _), 
    crStep(Images, Nodes, MaxR, Placement, [], OkPlacement, Alloc, KOImages), %dif(Images,KOImages),
    placement(KOImages, Nodes, MaxR, OkPlacement, NewPlacement, Cost).   

/* Identifies images to be replaced (i.e. new images or images with problems on storage or transfer times) */
crStep([I|Is], Nodes, MaxR, P, POk, NewPOk, Alloc, KO) :-
    findall(at(I,N), member(at(I,N), P), INs), append(INs, POk, TmpPOk),
    length(INs, IReplicas), IReplicas =< MaxR,
    transferTimesOk(I, Nodes, TmpPOk),
    image(I, Size, _), storageOk(I, Size, TmpPOk, Alloc), !,
    crStep(Is, Nodes, MaxR, P, TmpPOk, NewPOk, Alloc, KO).
crStep([I|Is], Nodes, MaxR, P, POk, NewPOk, Alloc, [I|KO]) :-
    crStep(Is, Nodes, MaxR, P, POk, NewPOk, Alloc, KO).
crStep([], _, _, _, POk, POk, _, []).

bestPlacement(P, Cost) :-
    imagesToPlace(Images), networkNodes(Nodes), maxReplicas(MaxR),
    placement(Images, Nodes, MaxR, [], P, Cost),
    \+ ( placement(Images, Nodes, MaxR, [], P2, C2), dif(P,P2), C2 < Cost ).

/* Iterative deepening */
placement([I|Mages], Nodes, MaxR, PartialPlacement, Placement, Cost) :-
    iterativeDeepening([I|Mages], Nodes, PartialPlacement, Placement, 1, MaxR), 
    cost(Placement, Cost),
    allocatedStorage(Placement,Alloc),
    storePlacement(Placement, Alloc, Cost).
placement([], _, _, POk, POk, Cost) :-
    cost(POk, Cost), allocatedStorage(POk,Alloc),
    storePlacement(POk, Alloc, Cost).  

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
    transferTime(I,M,N,T),
    T < MaxR, !, % one source is enough
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
    (placedImages(_, Alloc, _) ; (Alloc = [])),
    node(N, Storage, _),
    findall(S, member((N,S), Alloc), OldAllocs), sumlist(OldAllocs, OldAlloc),
    usedHw(Placement, N, UsedHw),
    Storage + OldAlloc - UsedHw >= Size.

cost(Placement, Cost) :- findall(CS, (member(at(I,N),Placement), image(I,S,_), node(N,_,C), CS is C*S), CSs), sum_list(CSs, Cost).

usedHw(P, N, TotUsed) :- findall(S, (member(at(I,N), P), image(I,S,_)), Used), sum_list(Used, TotUsed).

allocatedStorage(P, Alloc) :- findall((N,S), (member(at(I,N), P), image(I,S,_)), Alloc).

storePlacement(Placement, Alloc, Cost) :-
    ( placedImages(_,_,_) -> retract(placedImages(_,_,_)) ; true),
    assert(placedImages(Placement, Alloc, Cost)).

%%% Utils %%%
loadFile(Filename, ToRetract) :-
    open(Filename, read, Str),
	maplist(retractall,ToRetract),
    readAndAssert(Str). 

readAndAssert(Str) :-
    read(Str, X), (X == end_of_file -> close(Str) ; assert(X), readAndAssert(Str)).

% Load ASP placement
% exploits temporarily loaded at/2 facts, computes allocatedStorage/2 and cost/2, then stores the result
% retracts temporary at/2 facts and previous placedImages/3 fact
loadASP() :- once(loadASPPlacement()).
loadASPPlacement() :-
    findall(at(I,N), at(I,N), Placement),
    %write('asserting new ASP placement: '), writeln(Placement),
    allocatedStorage(Placement, Alloc), cost(Placement, Cost),
    (retractall(at(_,_)); true), storePlacement(Placement, Alloc, Cost).