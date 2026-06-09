"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { SimpleSelect } from "@/components/ui/simple-select";
import { Textarea } from "@/components/ui/textarea";
import { CharacterCard, CharacterCardPayload, CharacterCardStatus, CharacterGender, resolveAssetUrl } from "@/lib/api";

export type CharacterCardForm = {
  name: string;
  gender: CharacterGender | "";
  role_type: string;
  identity: string;
  background: string;
  personality: string;
  goal: string;
  motivation: string;
  secret: string;
  conflict_points: string;
  relationship_notes: string;
  speech_style: string;
  catchphrases: string;
  emotional_arc: string;
  story_function: string;
  visual_description: string;
  image_keywords: string;
  reference_image_url: string;
  reference_local_path: string;
  turnaround_prompt: string;
  status: CharacterCardStatus;
};

export const roleTypes = ["复仇者", "守护者", "操控者", "成长型", "权力型", "治愈型", "探索者", "其他"];
export const genderOptions: CharacterGender[] = ["男", "女"];

export const statuses: { label: string; value: "" | CharacterCardStatus }[] = [
  { label: "全部状态", value: "" },
  { label: "草稿", value: "draft" },
  { label: "可加载", value: "active" },
  { label: "已归档", value: "archived" }
];

export const emptyCharacterCardForm: CharacterCardForm = {
  name: "",
  gender: "",
  role_type: "成长型",
  identity: "",
  background: "",
  personality: "",
  goal: "",
  motivation: "",
  secret: "",
  conflict_points: "",
  relationship_notes: "",
  speech_style: "",
  catchphrases: "",
  emotional_arc: "",
  story_function: "",
  visual_description: "",
  image_keywords: "",
  reference_image_url: "",
  reference_local_path: "",
  turnaround_prompt: "",
  status: "draft"
};

type CharacterCardFormViewProps = {
  form: CharacterCardForm;
  onChange: (field: keyof CharacterCardForm, value: string) => void;
  disabled?: boolean;
  hideStatusField?: boolean;
};

export function CharacterCardFormView({ form, onChange, disabled = false, hideStatusField = false }: CharacterCardFormViewProps) {
  // 旧角色卡可能仍保存“主角/反派/配角”等旧版角色类型，编辑时需要展示原值并避免保存时被静默改写。
  const roleOptions = roleTypes.includes(form.role_type) || !form.role_type ? roleTypes : [form.role_type, ...roleTypes];

  return (
    <div className="stack">
      <section className="form-section stack">
        <h3>基础身份</h3>
        <div className="grid-2">
          <InputField
            disabled={disabled}
            label="角色名"
            field="name"
            form={form}
            onChange={onChange}
            placeholder="例如：沈砚、林晚、顾知衡"
            hint="角色在资产库中的主标识，建议使用短剧中实际出现的名字。"
          />
          <div className="field">
            <label>性别</label>
            <SimpleSelect
              disabled={disabled}
              value={form.gender}
              onValueChange={(value) => onChange("gender", value)}
              options={[{ label: "请选择性别", value: "" }, ...genderOptions.map((gender) => ({ label: gender, value: gender }))]}
            />
            <span className="field-hint">性别会用于人物设定、对白称谓和三视图生成，只支持男或女。</span>
          </div>
          <div className="field">
            <label>人物原型</label>
            <SimpleSelect
              disabled={disabled}
              value={form.role_type}
              onValueChange={(value) => onChange("role_type", value)}
              options={roleOptions.map((role) => ({ label: role, value: role }))}
            />
            <span className="field-hint">选择跨项目稳定的人设原型，例如复仇者、守护者、操控者或成长型。</span>
          </div>
        </div>
        <InputField
          disabled={disabled}
          label="身份摘要"
          field="identity"
          form={form}
          onChange={onChange}
          placeholder="例如：表面温顺、暗中布局的豪门女主"
          hint="用一句话说明角色最核心的身份和戏剧张力。"
        />
        {!hideStatusField && (
          <div className="field">
            <label>状态</label>
            <SimpleSelect
              disabled={disabled}
              value={form.status}
              onValueChange={(value) => onChange("status", value)}
              options={[
                { label: "草稿", value: "draft" },
                { label: "可加载", value: "active" },
                { label: "已归档", value: "archived" }
              ]}
            />
            <span className="field-hint">草稿用于未完成角色；可加载状态才能加入项目。</span>
          </div>
        )}
      </section>

      <section className="form-section stack">
        <h3>人物资产设定</h3>
        <div className="grid-2">
          <TextAreaField disabled={disabled} label="人物背景" field="background" form={form} onChange={onChange} placeholder="例如：幼年被家族边缘化，成年后以投资人身份回归。" hint="写清跨项目稳定的出身、经历和处境，不写具体项目集数剧情。" />
          <TextAreaField disabled={disabled} label="性格" field="personality" form={form} onChange={onChange} placeholder="例如：外冷内热、极强控制欲、习惯先观察再行动。" hint="描述稳定性格特征，避免只写单个形容词。" />
          <TextAreaField disabled={disabled} label="核心欲望 / 人物执念" field="goal" form={form} onChange={onChange} placeholder="例如：证明自身价值、掌控命运、守护亲人、摆脱被安排的人生。" hint="描述角色跨项目稳定的内在驱动力，不填写某个项目的具体剧情目标。" />
        </div>
      </section>

      <section className="form-section stack">
        <h3>口吻与视觉设定</h3>
        <div className="grid-2">
          <TextAreaField disabled={disabled} label="说话方式" field="speech_style" form={form} onChange={onChange} placeholder="例如：语速慢、很少解释、常用反问压迫对方。" hint="后续生成对白时会参考这里。" />
          <TextAreaField disabled={disabled} label="常用表达" field="catchphrases" form={form} onChange={onChange} placeholder="例如：你确定要知道真相吗？\n这笔账，我记了很多年。" hint="每行一条，沉淀口头禅或习惯表达。" />
          <TextAreaField disabled={disabled} label="视觉描述" field="visual_description" form={form} onChange={onChange} placeholder="例如：28 岁左右，冷静克制，黑色长发，浅色西装，眼神疏离但有攻击性。" hint="用于人物三视图和后续视频一致性参考。" />
          <TextAreaField disabled={disabled} label="形象关键词" field="image_keywords" form={form} onChange={onChange} placeholder="例如：冷感、精英感、黑长直、浅色西装、克制、危险感" hint="建议 3 到 12 个关键词，快速约束视觉方向。" />
        </div>
        <ReferencePreview url={form.reference_image_url} />
      </section>
    </div>
  );
}

function TextAreaField({
  label,
  field,
  form,
  onChange,
  disabled,
  placeholder,
  hint
}: {
  label: string;
  field: keyof CharacterCardForm;
  form: CharacterCardForm;
  onChange: (field: keyof CharacterCardForm, value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <Textarea disabled={disabled} value={form[field]} onChange={(event) => onChange(field, event.target.value)} placeholder={placeholder} />
      {hint ? <span className="field-hint">{hint}</span> : null}
    </div>
  );
}

function InputField({
  label,
  field,
  form,
  onChange,
  disabled,
  placeholder,
  hint
}: {
  label: string;
  field: keyof CharacterCardForm;
  form: CharacterCardForm;
  onChange: (field: keyof CharacterCardForm, value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <Input disabled={disabled} value={form[field]} onChange={(event) => onChange(field, event.target.value)} placeholder={placeholder} />
      {hint ? <span className="field-hint">{hint}</span> : null}
    </div>
  );
}

export function ReferencePreview({ url }: { url: string }) {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setHasError(false);
  }, [url]);

  if (!url.trim()) {
    return <div className="image-placeholder">未上传参考图。保存角色卡后可在详情页上传人物氛围图、服装参考或脸部风格参考。</div>;
  }

  return (
    <div className="reference-preview">
      {hasError ? (
        <div className="image-placeholder">参考图无法预览，请重新上传图片。</div>
      ) : (
        // 预览只读取后端返回的素材访问地址，不暴露本地文件系统路径。
        <img src={resolveAssetUrl(url)} alt="角色参考图预览" onError={() => setHasError(true)} />
      )}
    </div>
  );
}

export function TurnaroundPromptField({
  form,
  onChange,
  disabled = false
}: {
  form: CharacterCardForm;
  onChange: (field: keyof CharacterCardForm, value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="field turnaround-prompt-field">
      <label>三视图提示词</label>
      <Textarea
        disabled={disabled}
        value={form.turnaround_prompt}
        onChange={(event) => onChange("turnaround_prompt", event.target.value)}
        placeholder="例如：全身角色设计，正面、侧面、背面，统一服装，干净背景，短剧人物设定图。"
      />
      <span className="field-hint">
        可先点击“生成提示词”自动拼接，再手动补充年龄、体型、发型、服装、气质、色彩和风格；不要指定模仿现实人物。
      </span>
    </div>
  );
}

export function validateCharacterCard(form: CharacterCardForm) {
  if (!form.name.trim()) {
    return "角色名不能为空。";
  }
  if (!form.gender) {
    return "性别不能为空。";
  }
  if (!form.role_type.trim()) {
    return "人物原型不能为空。";
  }
  if (!form.identity.trim()) {
    return "身份摘要不能为空。";
  }
  if (!form.goal.trim()) {
    return "核心欲望 / 人物执念不能为空。";
  }
  return "";
}

export function validateTurnaroundPromptFields(form: CharacterCardForm) {
  if (!form.name.trim() || !form.gender || !form.identity.trim()) {
    return "请先填写角色名、性别和身份摘要后再生成提示词。";
  }
  return "";
}

export function buildTurnaroundPrompt(form: CharacterCardForm, includeCurrentPrompt = true) {
  const parts = [
    "请生成同一角色的人物三视图，画面包含正面、侧面、背面，全身，统一服装，干净背景。",
    "输出应适合作为短剧人物视觉参考，不模仿任何特定现实人物。",
    fieldLine("角色名", form.name),
    fieldLine("性别", form.gender),
    fieldLine("身份摘要", form.identity),
    fieldLine("视觉描述", form.visual_description),
    fieldLine("形象关键词", form.image_keywords),
    fieldLine("人物原型", form.role_type),
    fieldLine("性格", form.personality),
    fieldLine("核心欲望 / 人物执念", form.goal),
    fieldLine("用户三视图补充", includeCurrentPrompt ? form.turnaround_prompt : "")
  ].filter(Boolean);

  if (form.reference_image_url.trim()) {
    // 自动提示词只描述参考图用途，不写入本地路径，避免把本机文件系统信息暴露给模型或用户。
    parts.push("参考图说明：参考图用于服装、脸部风格或整体氛围参考。");
  }

  return parts.join("\n");
}

export function formToPayload(form: CharacterCardForm): CharacterCardPayload {
  return {
    name: form.name,
    gender: toGender(form.gender),
    role_type: form.role_type,
    identity: form.identity,
    background: optionalText(form.background),
    personality: optionalText(form.personality),
    goal: form.goal,
    motivation: optionalText(form.motivation),
    secret: optionalText(form.secret),
    conflict_points: optionalText(form.conflict_points),
    relationship_notes: optionalText(form.relationship_notes),
    speech_style: optionalText(form.speech_style),
    catchphrases: optionalText(form.catchphrases),
    emotional_arc: optionalText(form.emotional_arc),
    story_function: optionalText(form.story_function),
    visual_description: optionalText(form.visual_description),
    image_keywords: optionalText(form.image_keywords),
    reference_image_url: optionalText(form.reference_image_url),
    reference_local_path: optionalText(form.reference_local_path),
    turnaround_prompt: optionalText(form.turnaround_prompt),
    status: form.status
  };
}

export function cardToForm(card: CharacterCard): CharacterCardForm {
  return {
    name: card.name ?? "",
    gender: card.gender ?? "",
    role_type: card.role_type ?? "成长型",
    identity: card.identity ?? "",
    background: card.background ?? "",
    personality: card.personality ?? "",
    goal: card.goal ?? "",
    motivation: card.motivation ?? "",
    secret: card.secret ?? "",
    conflict_points: card.conflict_points ?? "",
    relationship_notes: card.relationship_notes ?? "",
    speech_style: card.speech_style ?? "",
    catchphrases: card.catchphrases ?? "",
    emotional_arc: card.emotional_arc ?? "",
    story_function: card.story_function ?? "",
    visual_description: card.visual_description ?? "",
    image_keywords: card.image_keywords ?? "",
    reference_image_url: card.reference_image_url ?? "",
    reference_local_path: card.reference_local_path ?? "",
    turnaround_prompt: card.turnaround_prompt ?? "",
    status: card.status
  };
}

export function statusLabel(status: CharacterCardStatus) {
  if (status === "active") return "可加载";
  if (status === "archived") return "已归档";
  return "草稿";
}

function optionalText(value: string) {
  return value.trim() || undefined;
}

function fieldLine(label: string, value: string) {
  const text = value.trim();
  return text ? `${label}：${text}` : "";
}

function toGender(value: CharacterCardForm["gender"]): CharacterGender {
  if (value === "男" || value === "女") {
    return value;
  }
  // formToPayload 只能在前端校验通过后调用，这里保留防御性错误，避免错误数据进入 API。
  throw new Error("性别不能为空。");
}
