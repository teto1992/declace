%%%%% FACT SCHEMA
% image(ID, Size, MaxTransferTime)
% max_replicas(ID, R)
% node(ID, Storage, Cost)
% link(I, J, Latency, Bandwidth)
%%%%%% 

% Each image is deployed to at least one node,
max_replicas(Img,R) :- image(Img,_,_), maxReplicas(R).
1 { placement(Img, NodeID): node(NodeID, _, _)} R :- image(Img, _, _), max_replicas(Img,R).

% Compute transfer times
transfer_time(Img, Src, Src, 0) :- placement(Img,Src). 
transfer_time(Img, Src, Dst, @compute_transfer_time(S,B,L)) :- placement(Img,Src), image(Img, S, _), link(Src, Dst, L, B).

% There exists a node X such that Img is deployed on X and X can transfer to Dst within thresholds
transfer_ok(Img,Dst)     :- transfer_time(Img, X, Dst,T), image(Img,_,MaxTransferTime), T <= (MaxTransferTime * 1000).
:- image(Img,_,_), node(Dst, _, _), not transfer_ok(Img, Dst).

% Storage threshold
:- TS = #sum{Size, Img : image(Img, Size, _), placement(Img, X)}, node(X, Cap, _), TS > Cap.

% Minimize costs 
:~ placement(Img, X), node(X, _, Cost), image(Img, Size, _). [Cost * Size @ 1, Img, X]

#show.
#show placement(image(Img,Size,TransferTime),X): placement(Img,X), image(Img,Size,TransferTime).