export interface IHistoryGraph {
  edges: IHistoryEdge[];
  nodes: (IHistoryNodeIndividual | IHistoryNodeOperator)[];
}

export interface IHistoryEdge {
  source: string;
  target: string;
}

export interface IHistoryNodeIndividual{
  uid: string;
  type: string;
  individual_id: any;
  full_name?: any;
  objs?: any;
  gen_id: number;
  ind_id: number;
};

export interface IHistoryNodeOperator {
  uid: string;
  type: string;
  full_name?: any;
  prev_gen_id: number;
  next_gen_id: number;
  operator_id: number;
  name: string[];
};
