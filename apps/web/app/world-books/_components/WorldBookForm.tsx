"use client";

import { WorldBook, WorldBookPayload, WorldBookStatus } from "@/lib/api";

export type WorldBookForm = {
  name: string;
  genre: string;
  era_background: string;
  world_rules: string;
  organizations: string;
  locations: string;
  social_structure: string;
  taboo_or_constraints: string;
  tone_style: string;
  summary: string;
  status: WorldBookStatus;
};

export const worldBookGenres = ["都市情感", "豪门恩怨", "悬疑复仇", "古风权谋", "奇幻异能", "职场商战", "校园青春", "其他"];

export const worldBookStatuses: { label: string; value: "" | WorldBookStatus }[] = [
  { label: "全部状态", value: "" },
  { label: "草稿", value: "draft" },
  { label: "可加载", value: "active" },
  { label: "已归档", value: "archived" }
];

export const emptyWorldBookForm: WorldBookForm = {
  name: "",
  genre: "都市情感",
  era_background: "",
  world_rules: "",
  organizations: "",
  locations: "",
  social_structure: "",
  taboo_or_constraints: "",
  tone_style: "",
  summary: "",
  status: "draft"
};

type WorldBookFormViewProps = {
  form: WorldBookForm;
  onChange: (field: keyof WorldBookForm, value: string) => void;
  disabled?: boolean;
  hideStatusField?: boolean;
};

export function WorldBookFormView({ form, onChange, disabled = false, hideStatusField = false }: WorldBookFormViewProps) {
  const genreOptions = worldBookGenres.includes(form.genre) || !form.genre ? worldBookGenres : [form.genre, ...worldBookGenres];

  return (
    <div className="stack">
      <section className="form-section stack">
        <h3>基础信息</h3>
        <div className="grid-2">
          <InputField
            disabled={disabled}
            label="世界观名称"
            field="name"
            form={form}
            onChange={onChange}
            placeholder="例如：雾港豪门、旧城异能局、云京权谋世界"
            hint="世界观在资产库中的主标识。"
          />
          <div className="field">
            <label>题材类型</label>
            <select disabled={disabled} value={form.genre} onChange={(event) => onChange("genre", event.target.value)}>
              {genreOptions.map((genre) => (
                <option key={genre} value={genre}>
                  {genre}
                </option>
              ))}
            </select>
            <span className="field-hint">用于列表筛选和生成时的题材方向。</span>
          </div>
        </div>
        <TextAreaField
          disabled={disabled}
          label="摘要"
          field="summary"
          form={form}
          onChange={onChange}
          placeholder="用 100 到 300 字概括这个世界观最重要的背景、冲突来源和风格。"
          hint="用于列表和项目加载预览。"
        />
        {!hideStatusField && (
          <div className="field">
            <label>状态</label>
            <select disabled={disabled} value={form.status} onChange={(event) => onChange("status", event.target.value)}>
              <option value="draft">草稿</option>
              <option value="active">可加载</option>
              <option value="archived">已归档</option>
            </select>
            <span className="field-hint">只有可加载状态的世界观可以加入项目。</span>
          </div>
        )}
      </section>

      <section className="form-section stack">
        <h3>核心设定</h3>
        <div className="grid-2">
          <TextAreaField disabled={disabled} label="时代背景" field="era_background" form={form} onChange={onChange} placeholder="例如：近未来海港城市，旧财团与新技术公司长期争夺城市资源。" hint="描述年代、地区、科技水平和社会环境。" />
          <TextAreaField disabled={disabled} label="核心世界规则" field="world_rules" form={form} onChange={onChange} placeholder="例如：所有异能者必须登记；豪门婚约可影响公司控制权；地下档案不可公开。" hint="生成内容必须遵守的硬规则。" />
          <TextAreaField disabled={disabled} label="社会结构或势力关系" field="social_structure" form={form} onChange={onChange} placeholder="例如：旧财团掌握资本和媒体，新技术公司掌握数据，普通人依附合同体系生存。" hint="写清阶层、势力关系和资源分配方式。" />
          <TextAreaField disabled={disabled} label="禁忌、限制或不可违反设定" field="taboo_or_constraints" form={form} onChange={onChange} placeholder="例如：主角不能公开暴露真实身份；某组织不能直接杀害继承人。" hint="用于避免后续生成破坏世界观边界。" />
        </div>
      </section>

      <section className="form-section stack">
        <h3>组织、地点与风格</h3>
        <div className="grid-2">
          <TextAreaField disabled={disabled} label="主要组织" field="organizations" form={form} onChange={onChange} placeholder="例如：沈氏财团、雾港调查局、黑石董事会。" hint="建议按行列出组织名称和核心功能。" />
          <TextAreaField disabled={disabled} label="主要地点" field="locations" form={form} onChange={onChange} placeholder="例如：雾港老城区、中央码头、沈氏顶层会议室。" hint="建议按行列出地点和可承载的戏剧功能。" />
          <TextAreaField disabled={disabled} label="整体风格" field="tone_style" form={form} onChange={onChange} placeholder="例如：高压、克制、反转密集，视觉上冷色、雨夜、玻璃幕墙和窄巷并置。" hint="约束叙事气质、视觉风格和对白风格。" />
        </div>
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
  field: keyof WorldBookForm;
  form: WorldBookForm;
  onChange: (field: keyof WorldBookForm, value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <textarea disabled={disabled} value={form[field]} onChange={(event) => onChange(field, event.target.value)} placeholder={placeholder} />
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
  field: keyof WorldBookForm;
  form: WorldBookForm;
  onChange: (field: keyof WorldBookForm, value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <input disabled={disabled} value={form[field]} onChange={(event) => onChange(field, event.target.value)} placeholder={placeholder} />
      {hint ? <span className="field-hint">{hint}</span> : null}
    </div>
  );
}

export function validateWorldBook(form: WorldBookForm) {
  if (!form.name.trim()) {
    return "世界观名称不能为空。";
  }
  if (!form.genre.trim()) {
    return "题材类型不能为空。";
  }
  if (!form.world_rules.trim()) {
    return "核心世界规则不能为空。";
  }
  return "";
}

export function formToPayload(form: WorldBookForm): WorldBookPayload {
  return {
    name: form.name,
    genre: form.genre,
    era_background: optionalText(form.era_background),
    world_rules: form.world_rules,
    organizations: optionalText(form.organizations),
    locations: optionalText(form.locations),
    social_structure: optionalText(form.social_structure),
    taboo_or_constraints: optionalText(form.taboo_or_constraints),
    tone_style: optionalText(form.tone_style),
    summary: optionalText(form.summary),
    status: form.status
  };
}

export function worldBookToForm(worldBook: WorldBook): WorldBookForm {
  return {
    name: worldBook.name ?? "",
    genre: worldBook.genre ?? "都市情感",
    era_background: worldBook.era_background ?? "",
    world_rules: worldBook.world_rules ?? "",
    organizations: worldBook.organizations ?? "",
    locations: worldBook.locations ?? "",
    social_structure: worldBook.social_structure ?? "",
    taboo_or_constraints: worldBook.taboo_or_constraints ?? "",
    tone_style: worldBook.tone_style ?? "",
    summary: worldBook.summary ?? "",
    status: worldBook.status
  };
}

export function worldBookStatusLabel(status: WorldBookStatus) {
  if (status === "active") return "可加载";
  if (status === "archived") return "已归档";
  return "草稿";
}

function optionalText(value: string) {
  return value.trim() || undefined;
}
