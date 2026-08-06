"""Fine-tune مدل با LoRA روی داده‌ی آموزشی + لاگ در W&B.

نیازمند GPU برای اجرای واقعی است (روی CPU خیلی کند می‌شود).
داده‌ی آموزشی: data/instruction_pairs.jsonl

استفاده:
    python -m scripts.train --model Qwen/Qwen2.5-0.5B-Instruct --epochs 3
"""
from __future__ import annotations
import argparse
import json
import os

import config


def load_dataset(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=config.GEN_MODEL)
    ap.add_argument("--data", default=os.path.join(config.DATA_DIR, "instruction_pairs.jsonl"))
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "model_lora"))
    args = ap.parse_args()

    # 1) W&B
    if config.WANDB_ENABLED:
        os.environ.setdefault("WANDB_PROJECT", config.WANDB_PROJECT)
        import wandb
        wandb.init(project=config.WANDB_PROJECT, entity=config.WANDB_ENTITY,
                   job_type="lora_finetune",
                   config=vars(args))
    else:
        print("⚠️ کلید WANDB_API_KEY نیست؛ بدون لاگ اجرا می‌شود.")

    # 2) مدل و توکایزر
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              TrainingArguments, Trainer, DataCollatorForLanguageModeling)
    from peft import LoraConfig, get_peft_model

    print("بارگذاری مدل:", args.model)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)

    lora_cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                          target_modules=["q_proj", "v_proj"],
                          task_type="CAUSAL_LM")
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # 3) داده
    rows = load_dataset(args.data)
    print("تعداد نمونه:", len(rows))

    def fmt(r):
        msg = [{"role": "system", "content": "دستیار بالینی پروتکل تشخیص دوگانه هستی. پاسخ کوتاه و بر اساس شواهد."},
               {"role": "user", "content": r["question"]},
               {"role": "assistant", "content": r["answer"]}]
        return tok.apply_chat_template(msg, tokenize=False, add_generation_prompt=False)

    texts = [fmt(r) for r in rows]

    class DS(torch.utils.data.Dataset):
        def __init__(self, t): self.t = tok(t, truncation=True, max_length=1024)
        def __len__(self): return len(self.t["input_ids"])
        def __getitem__(self, i): return {k: v[i] for k, v in self.t.items()}

    ds = DS(texts)

    targs = TrainingArguments(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        learning_rate=args.lr,
        logging_steps=5,
        save_strategy="epoch",
        report_to="wandb" if config.WANDB_ENABLED else "none",
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model, args=targs, train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tok, mlm=False),
    )
    trainer.train()
    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    print("✓ مدل ذخیره شد در", args.out)
    if config.WANDB_ENABLED:
        import wandb; wandb.finish()


if __name__ == "__main__":
    main()
