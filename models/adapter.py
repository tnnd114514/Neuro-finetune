import torch.nn as nn

class NeuroStyleAdapter(nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model
        self.style_proj = nn.Linear(1024, 256)
        
    def forward(self, input_ids, style_coeff=0.7):
        outputs = self.base_model(input_ids)
        logits = outputs.logits
        style_logits = self.style_proj(logits)
        return logits + style_coeff * style_logits
