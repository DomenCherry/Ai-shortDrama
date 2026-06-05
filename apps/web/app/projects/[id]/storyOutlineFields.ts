export type StoryOutlineTextFieldKey =
  | "logline"
  | "story_background"
  | "main_goal"
  | "core_conflict"
  | "story_start"
  | "ending_direction"
  | "plot_structure"
  | "reversals"
  | "emotion_curve"
  | "foreshadowing"
  | "character_arcs"
  | "pacing_advice"
  | "capacity_advice"
  | "notes";

export type StoryOutlineField = {
  key: StoryOutlineTextFieldKey;
  label: string;
  description: string;
  example: string;
};

export type StoryOutlineFieldGroup = {
  id: "core" | "structure" | "execution";
  title: string;
  description: string;
  fields: StoryOutlineField[];
};

export const storyOutlineFieldGroups: StoryOutlineFieldGroup[] = [
  {
    id: "core",
    title: "故事核心层",
    description: "定义整部故事讲什么、为什么开始、最终走向哪里。",
    fields: [
      {
        key: "logline",
        label: "一句话故事",
        description: "用一句话概括故事卖点、主角处境和主线方向。",
        example: "示例：一个被低估的人在重大变故后被迫反击，并在持续压迫中夺回身份与选择权。"
      },
      {
        key: "story_background",
        label: "故事背景",
        description: "描述故事启动前的基本局面，不替代完整世界观设定。",
        example: "示例：故事开始前，核心关系长期失衡，表面秩序稳定，但关键资源和真相被少数人掌控。"
      },
      {
        key: "main_goal",
        label: "主线目标",
        description: "说明整部故事持续推进的终极目标，分集目标应围绕它展开。",
        example: "示例：主角需要在限定时间内完成自我证明、揭开真相，并重建属于自己的秩序。"
      },
      {
        key: "core_conflict",
        label: "核心矛盾",
        description: "定义贯穿全剧的根本对立，比单集冲突更上层。",
        example: "示例：个人觉醒与既有权力结构的冲突，外部打压和内部动摇同时推动故事升级。"
      },
      {
        key: "story_start",
        label: "故事起点",
        description: "写清故事正式启动的触发事件，决定第一阶段从哪里开始。",
        example: "示例：一次公开羞辱或关键损失打破原有平衡，主角不得不做出无法回头的选择。"
      },
      {
        key: "ending_direction",
        label: "结局方向",
        description: "说明全剧最终走向，用来约束后续分集不能偏离主线。",
        example: "示例：主角完成目标，但结局不只是胜利，还要完成身份、关系或价值判断的确认。"
      }
    ]
  },
  {
    id: "structure",
    title: "结构规划层",
    description: "把全剧骨架拆成阶段、转折、情绪和伏笔方向。",
    fields: [
      {
        key: "plot_structure",
        label: "起承转合结构",
        description: "描述全剧阶段划分，不写成单集正文。",
        example: "示例：起：失衡与触发；承：试探反击；转：真相反噬；合：集中清算与关系重建。"
      },
      {
        key: "reversals",
        label: "阶段性反转",
        description: "记录全剧阶段级转折，不替代分集里的关键反转。",
        example: "示例：中段发现目标并非单一对手，后段发现胜利代价会反过来考验主角立场。"
      },
      {
        key: "emotion_curve",
        label: "情绪曲线",
        description: "规划观众情绪从压抑、期待到释放的变化。",
        example: "示例：前段压抑和不甘，中段爽感递增，后段紧张升级，结尾完成释放和余味。"
      },
      {
        key: "foreshadowing",
        label: "关键伏笔",
        description: "记录全剧级伏笔和回收方向，不替代每集具体埋点。",
        example: "示例：早期出现的异常承诺、物件或关系细节，在终局揭示真正含义并推动反转。"
      },
      {
        key: "character_arcs",
        label: "人物弧光",
        description: "描述主要人物的全剧变化方向，不替代角色卡。",
        example: "示例：主角从被动忍耐转向主动选择，对手从绝对掌控走向失控暴露。"
      }
    ]
  },
  {
    id: "execution",
    title: "执行辅助层",
    description: "给分集拆解和后续制作提供节奏、容量和补充约束。",
    fields: [
      {
        key: "pacing_advice",
        label: "整体节奏建议",
        description: "说明全剧节奏密度和阶段重点。",
        example: "示例：前 3 集快速建立钩子和压迫，中段每 2-3 集一次升级，后段减少支线并集中收束。"
      },
      {
        key: "capacity_advice",
        label: "剧情容量建议",
        description: "根据集数和单集时长判断剧情装载量。",
        example: "示例：每集只推进一个核心事件，重要支线合并处理，避免在短时长内同时展开过多人物线。"
      },
      {
        key: "notes",
        label: "补充说明",
        description: "记录用户特殊要求、禁忌、风格约束或临时备注。",
        example: "示例：避免过度解释设定，重点保留强冲突、强选择和每阶段清晰的情绪回报。"
      }
    ]
  }
];
