"""Publication-scale vector schematics, drawn from the implemented study.

Coordinates and text sizes are points at a 7.16-inch final publication width.
No empirical outcome values are authored here. Board counts come from data.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

WIDTH = 515.52
INK = "#24282B"
BLUE = "#396A85"
TEAL = "#447A6B"
GOLD = "#A77837"
PURPLE = "#76618A"
RED = "#AE544B"
FILLS = ("#EDF3F6", "#EFF5F1", "#FCF5E8", "#F2EFF6")


class Drawing:
    def __init__(self, height):
        self.fig = plt.figure(figsize=(WIDTH / 72, height / 72))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set(xlim=(0, WIDTH), ylim=(height, 0))
        self.ax.axis("off")

    def text(self, x, y, text, size=8.6, bold=False, color=INK, align="center", **kw):
        kw.setdefault("zorder", 6)
        return self.ax.text(x, y, text, fontsize=size, ha=align, va="center",
                            fontweight="bold" if bold else "normal", color=color,
                            linespacing=1.23, **kw)

    def box(self, x, y, w, h, text="", fill="white", edge=INK, size=8.6,
            bold=False, dash=False):
        self.ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                                    lw=.65, linestyle=(0, (3, 2)) if dash else "-", zorder=2))
        if text:
            self.text(x+w/2, y+h/2, text, size=size, bold=bold, zorder=3)

    def panel(self, x, y, w, h, title, fill, color):
        self.box(x, y, w, h, fill=fill, edge=color)
        self.box(x, y, w, 22, title, fill=color, edge=color, size=8.7, bold=True)
        # White section headers, black content text.
        self.ax.texts[-1].set_color("white")

    def route(self, points, color=INK, dash=False, arrow=True, lw=.85):
        style = (0, (3, 2)) if dash else "-"
        if len(points) > 2:
            self.ax.add_line(Line2D(*zip(*points[:-1]), color=color, lw=lw,
                                    linestyle=style, zorder=4))
        self.ax.add_patch(FancyArrowPatch(points[-2], points[-1],
                          arrowstyle="-|>" if arrow else "-", mutation_scale=7,
                          color=color, lw=lw, linestyle=style, shrinkA=0, shrinkB=0, zorder=4))

    def dot(self, x, y, color=INK):
        self.ax.add_patch(Circle((x, y), 1.4, color=color, zorder=5))

    def save(self, outdir, stem):
        outdir.mkdir(parents=True, exist_ok=True)
        paths = []
        for ext in ("pdf", "svg", "png"):
            path = outdir / f"{stem}.{ext}"
            meta = ({"Creator": "paper/diagram_art.py", "CreationDate": None, "ModDate": None}
                    if ext == "pdf" else {"Date": None, "Creator": "paper/diagram_art.py"}
                    if ext == "svg" else {"Software": "paper/diagram_art.py"})
            self.fig.savefig(path, dpi=400, bbox_inches=None, pad_inches=0, metadata=meta)
            paths.append(path)
        plt.close(self.fig)
        return paths


def training_diagram(outdir):
    d = Drawing(300)
    d.panel(1, 24, 109, 251, "(a) Frozen resources", FILLS[0], BLUE)
    d.panel(121, 24, 119, 251, "(b) Policy learning", FILLS[1], TEAL)
    d.panel(251, 24, 135, 251, "(c) Gated rewards", FILLS[2], GOLD)
    d.panel(397, 24, 117, 251, "(d) Physical test", FILLS[3], PURPLE)

    d.box(10, 56, 91, 39, "Accelerator families\nFIR / reverse FIR\npoly / IIR / median", size=8.4)
    d.box(10, 116, 91, 39, "Training designs\nverified RTL corpus\n+ design prompts", size=8.4)
    d.route([(55,95),(55,116)])
    d.box(10, 176, 91, 39, "Domain SFT\ncompletion-masked\nLoRA adapter", fill=FILLS[0], bold=False)
    d.route([(55,155),(55,176)])
    d.box(10, 230, 91, 37, "Measured train RTL\npost-route labels\nheld-out excluded", size=8.1)

    d.box(132, 56, 97, 39, "Trainable policy\ncurrent LoRA weights\n+ design prompt $d$", fill=FILLS[1])
    d.route([(101,195),(115,195),(115,76),(132,76)], color=BLUE)
    # A stack denotes multiple emitted completions, not a generic LLM logo.
    for delta in (6, 3, 0):
        d.box(132+delta, 119-delta, 91, 40, fill="white", edge=TEAL)
    d.text(177.5,130,"Sample a group",bold=True)
    d.text(177.5,148,r"$m_1,\ldots,m_G\sim\pi_\theta$",size=9)
    d.route([(180,95),(180,113)])
    d.box(132, 201, 97, 49, "Group-relative update\nnormalize rewards\nmean-token log-prob.\nreference regularizer", size=8.3, fill=FILLS[1])
    d.box(132, 258, 97, 15, "Frozen SFT reference", size=8.0, dash=True)
    d.route([(180,258),(180,250)],dash=True,color=BLUE)
    d.route([(132,225),(126,225),(126,76),(132,76)],color=TEAL,dash=True)
    d.text(180,177,"Flat group: skip update",size=8.0,color=TEAL)

    d.box(262, 56, 110, 39, "Executable oracle\ncompile + simulate\nlatency-aligned tests",size=8.5)
    d.route([(229,139),(245,139),(245,76),(262,76)])
    d.route([(317,95),(317,113)],color=TEAL)
    d.text(326,105,"pass",size=8,color=TEAL,align="left")
    d.box(262,113,110,95,fill="white",edge=GOLD)
    d.text(317,124,"RF reward package",bold=True,color=GOLD)
    d.box(269,135,96,20,"Canonicalize + compile",size=8)
    d.route([(317,155),(317,163)])
    d.box(269,163,96,20,"Structural features",size=8.3)
    d.route([(317,183),(317,189)])
    d.text(317,198,"RF → clamp → exp",size=8.5)
    # The frozen measured corpus fits the RF; it is not per-update EDA.
    d.route([(101,248),(116,248),(116,189),(262,189)],color=BLUE)
    d.text(185,194,"fit once",size=7.8,color=BLUE)
    d.box(262,220,110,30,"Alternative reward arms\noriginal MLP / correctness",size=8.1)
    d.route([(317,100),(379,100),(379,235),(372,235)],color=GOLD,dash=True)
    d.box(262,258,110,15,"Rejected candidate: $R=0$",fill="#FAEFED",edge=RED,size=8)
    d.route([(372,72),(383,72),(383,265),(372,265)],color=RED)
    d.text(378,59,"fail",size=7.8,color=RED)
    d.route([(365,145),(383,145)],color=RED,arrow=False)
    d.dot(383,145,RED)
    # Common reward-return bus; dashed alternatives denote separate runs.
    for y in (201,243,269):
        d.route([(372,y),(391,y)],color=GOLD,arrow=False)
    d.route([(391,201),(391,283),(234,283),(234,244),(229,244)],color=GOLD)
    d.text(288,292,"Scalar reward; same update rule across arms",size=8,color=GOLD)

    d.box(407,56,97,39,"Frozen checkpoints\nSFT / RF / MLP /\ncorrectness only",size=8.4)
    d.route([(229,66),(245,66),(245,12),(391,12),(391,51),(455,51),(455,56)],color=PURPLE,dash=True)
    d.text(325,5,"Checkpoint freeze + pre-open gates",size=8,color=PURPLE)
    d.box(407,113,97,32,"Held-out generation\nfixed draw budget $n_d$",size=8.4)
    d.route([(455,95),(455,113)],color=PURPLE)
    d.box(407,159,97,28,"Held-out oracle",size=8.8)
    d.route([(455,145),(455,159)])
    d.box(407,201,97,30,"Distinct passing RTL\nVivado synth/place/route",size=8)
    d.route([(455,187),(455,201)],color=TEAL)
    d.box(407,238,97,35,fill=FILLS[3])
    d.text(455,246,"Restore multiplicity",size=8.3)
    d.text(455,261,r"$\bar{F}=\sum_m c_m F_m/n_d$",size=8.5)
    d.route([(455,231),(455,238)])
    d.route([(407,173),(401,173),(401,260),(407,260)],color=RED)
    d.route([(407,216),(401,216)],color=RED,arrow=False)
    d.dot(401,216,RED)
    d.text(455,290,"Failures contribute zero",size=8,color=RED)
    return d.save(outdir,"fig01_training_evidence_boundary_v3")


def board_diagram(data, outdir):
    d = Drawing(270)
    d.panel(1,4,124,255,"(a) Candidate contract",FILLS[0],BLUE)
    d.panel(137,4,258,255,"(b) PYNQ-Z2 test harness",FILLS[1],TEAL)
    d.panel(407,4,107,255,"(c) Trace validation",FILLS[3],PURPLE)
    d.box(11,36,104,36,"Correctness-eligible pairs\nfamily-wise fixed hash\namended before sweeps",size=8.1)
    d.box(11,90,104,39,"Identical SFT / RF rule\nmaximum multiplicity\nRTL-hash tie-break",size=8.3)
    d.route([(63,72),(63,90)])
    d.box(11,151,104,32,"DUT / golden self-check\nimplementation gate",size=8.3)
    d.route([(63,129),(63,151)])
    d.box(11,211,104,39,"Frozen image bundle\nbitstream + HWH\nselectors + manifest",size=8.5,fill=FILLS[0])
    d.route([(63,183),(63,211)])

    d.box(149,36,234,38,fill="white",edge=TEAL)
    d.text(266,46,"Processing system (PS)",bold=True)
    d.text(266,62,"Python sweep controller · MMIO · programmable FCLK",size=8.1)
    d.box(147,93,238,158,fill="white",edge=TEAL)
    d.text(266,104,"Programmable logic (PL): one co-resident image",size=8.1,bold=True)
    d.route([(115,230),(131,230),(131,84),(161,84),(161,74)],color=BLUE)
    d.text(190,84,"load once",size=8,color=BLUE)
    d.box(154,151,47,40,"Counter\nstimulus",size=8.4)
    d.box(216,133,76,70,fill=FILLS[0])
    d.text(235,142,"SFT",size=8,bold=True,color=BLUE)
    d.text(273,142,"RF",size=8,bold=True,color=TEAL)
    for index, label in enumerate(("FIR", "rFIR", "poly", "IIR", "med")):
        y=149+index*10
        d.box(221,y,29,9,label,fill="#DCE8EF",edge=BLUE,size=7.3)
        d.box(259,y,29,9,label,fill="#E0ECE5",edge=TEAL,size=7.3)
    d.box(216,215,76,20,"Echo canary",size=8.4,fill=FILLS[2],edge=GOLD)
    d.route([(201,171),(208,171),(216,171)])
    d.route([(208,171),(208,225),(216,225)])
    d.dot(208,171)
    d.ax.add_patch(Polygon([(307,156),(326,166),(326,206),(307,216)],
                          closed=True,facecolor="#F5F5F4",edgecolor=INK,lw=.7,zorder=2))
    d.text(316,186,"MUX",size=7.5,rotation=90)
    d.route([(292,171),(307,171)])
    d.route([(292,225),(300,225),(300,204),(307,204)])
    d.box(343,162,34,49,"Capture\nbuffer\nAXI-lite",size=7.6)
    d.route([(326,186),(343,186)])
    d.route([(383,56),(391,56),(391,176),(377,176)],color=BLUE)
    d.text(398,134,"MMIO",size=7.8,rotation=90,color=BLUE)
    d.route([(377,200),(388,200),(388,66),(383,66)],color=BLUE)
    d.route([(174,74),(143,74),(143,120),(178,120),(178,151)],color=TEAL,dash=True)
    d.route([(178,120),(244,120)],color=TEAL,dash=True,arrow=False)
    d.route([(244,120),(254,120),(254,133)],color=TEAL,dash=True)
    d.route([(254,120),(333,120),(333,154),(343,154),(343,162)],color=TEAL,dash=True)
    d.text(191,116,"FCLK",size=7.7,color=TEAL)
    d.route([(343,200),(334,200),(334,243),(178,243),(178,191)],color=BLUE,dash=True)
    d.text(260,244,"capture / reset control",size=7.8,color=BLUE,
           bbox=dict(facecolor="white",edgecolor="none",pad=.4))
    d.route([(343,170),(333,170),(333,145),(316,145),(316,161)],color=BLUE,dash=True)
    d.text(317,137,"sel",size=8,color=BLUE)

    d.box(416,36,89,42,"Captured traces\nfixed clock grid\nrepeated sweeps",size=8.2)
    d.route([(383,46),(416,46)])
    d.box(416,96,89,33,"Per-DUT golden\nreference stream",size=8.4)
    d.box(416,151,89,39,"Latency alignment\nscore threshold\ncanary headroom",size=8.2)
    d.route([(460,129),(460,151)])
    d.route([(505,57),(510,57),(510,171),(505,171)])
    d.box(416,215,89,32,"Clock boundaries\nall paired outcomes",size=8.3,fill=FILLS[3])
    d.route([(460,190),(460,215)])
    d.text(258,266,"Solid: data / execution path     Dashed: control / frozen-reference path",size=8)
    return d.save(outdir,"fig04_board_architecture_v2")
