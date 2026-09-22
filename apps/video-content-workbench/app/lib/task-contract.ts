export const TASK_TYPES = ["pipeline", "quick-copy"] as const;
export const TASK_STATUSES = ["queued", "processing", "review", "completed", "failed", "cancelled"] as const;
export const PIPELINE_STAGES = ["material", "analysis", "rewrite", "review", "platforms", "export"] as const;
export const QUICK_COPY_STAGES = ["material", "generating", "result"] as const;

export type TaskType = (typeof TASK_TYPES)[number];
export type TaskStatus = (typeof TASK_STATUSES)[number];
export type TaskStage = (typeof PIPELINE_STAGES)[number] | (typeof QUICK_COPY_STAGES)[number];

export type TaskSource = {
  name: string;
  mediaType: string;
  size: number;
};

export type VideoWorkflowResult = {
  contract_version: "video-workflow/1.0";
  source_name: string;
  language: string;
  language_probability?: number;
  duration_seconds?: number;
  inference: "local faster-whisper; OpenAI API not used";
  segments: Array<{
    start: number;
    end: number;
    text: string;
    avg_logprob?: number;
    compression_ratio?: number;
    no_speech_prob?: number;
  }>;
  transcription_quality?: {
    needs_visual_review?: boolean;
    review_reasons?: string[];
  };
  enrichment: {
    mode: "full" | "extract-only";
    translation?: string;
    rewrite?: string;
    analysis?: Record<string, unknown>;
    ollama_model?: string;
    brand?: string;
    brand_url?: string;
  };
};

export type WorkbenchTask = {
  contractVersion: "video-content-task/1.0";
  id: string;
  name: string;
  type: TaskType;
  status: TaskStatus;
  stage: TaskStage;
  progress: number;
  createdAt: string;
  updatedAt: string;
  source: TaskSource | null;
  settings: {
    brand: string;
    brandUrl: string;
    market: string;
    language: string;
  };
  error: {
    code: string;
    message: string;
    recoverable: boolean;
  } | null;
  result?: VideoWorkflowResult | null;
};

export const statusLabels: Record<TaskStatus, string> = {
  queued: "等待处理",
  processing: "处理中",
  review: "待审核",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
};

export const stageLabels: Record<TaskStage, string> = {
  material: "素材",
  analysis: "分析",
  rewrite: "改写",
  review: "审核",
  platforms: "六平台适配",
  export: "导出",
  generating: "生成中",
  result: "结果",
};
