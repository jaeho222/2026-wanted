// contracts/opinionmap.schema.json 과 일치하는 타입

export type Stance = "positive" | "negative" | "neutral";
export type RelationType = "support" | "attack" | "related";

export interface Claim {
  id: string;
  text: string;
  count: number;
  stance: Stance;
  sample_comments: string[];
}

export interface Relation {
  from: string;
  to: string;
  type: RelationType;
}

export interface HiddenOpinion {
  text: string;
  share: number;
  top_share: number;
}

export interface OpinionMap {
  topic: string;
  meta?: {
    total_comments?: number;
    topic_count?: number;
    claim_count?: number;
  };
  claims: Claim[];
  relations: Relation[];
  hidden_opinions: HiddenOpinion[];
}
