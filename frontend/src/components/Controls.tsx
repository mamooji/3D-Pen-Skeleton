import { useState } from "react";
import { ChevronDown, Info } from "lucide-react";
import type { Params } from "../api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Props {
  params: Params;
  resolved?: Params;
  /** The width the last template used, shown while the width is automatic. */
  widthCm?: number | null;
  onChange: (p: Params) => void;
}

const DETAIL_LABELS = [
  "",
  "Very simple",
  "Simple",
  "Balanced",
  "Detailed",
  "Very detailed",
];

const SHAPE_LABELS = ["Round", "Slightly boxy", "Boxy", "Very boxy", "Brick"];

export default function Controls({
  params,
  resolved,
  widthCm,
  onChange,
}: Props) {
  const [advanced, setAdvanced] = useState(false);
  const set = (patch: Partial<Params>) => onChange({ ...params, ...patch });
  const boxy = params.shape > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Settings</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <SliderField
          id="detail"
          label="Detail"
          help="More ribs and rings and finer curves. Changing it resets manual rib and ring counts."
          value={params.detail}
          min={1}
          max={5}
          step={1}
          display={DETAIL_LABELS[params.detail]}
          onChange={(v) => set({ detail: v, ribs: null, rings: null })}
        />
        <SliderField
          id="size"
          label="Size"
          help="Printed length of the object's longest side."
          value={params.size_cm}
          min={5}
          max={40}
          step={0.5}
          display={`${params.size_cm} cm`}
          onChange={(v) => set({ size_cm: v })}
        />
        <SliderField
          id="shape"
          label="Shape"
          help="Round suits animals, fruit and characters. Boxy gives flat sides and a real width, for cars, boxes and furniture."
          value={params.shape}
          min={0}
          max={4}
          step={1}
          display={SHAPE_LABELS[params.shape]}
          onChange={(v) => set({ shape: v })}
        />
        {boxy ? (
          <SliderField
            id="width"
            label="Width"
            help="How wide the object is side to side, at the printed size. It starts at a guess from the length; a car is about 40% as wide as it is long."
            value={params.width_cm ?? widthCm ?? params.size_cm * 0.4}
            min={1}
            max={40}
            step={0.5}
            display={
              params.width_cm === null
                ? `${widthCm ?? "…"} cm (auto)`
                : `${params.width_cm} cm`
            }
            onChange={(v) => set({ width_cm: v })}
          />
        ) : (
          <SliderField
            id="thickness"
            label="Thickness"
            help="How deep the object is front to back, compared with a rounded guess from the photo."
            value={params.thickness}
            min={0.3}
            max={2}
            step={0.05}
            display={`${Math.round(params.thickness * 100)}%`}
            onChange={(v) => set({ thickness: v })}
          />
        )}

        <div className="flex items-center justify-between gap-4">
          <Label htmlFor="paper">Paper</Label>
          <Select
            value={params.paper}
            onValueChange={(v) => set({ paper: v as Params["paper"] })}
          >
            <SelectTrigger id="paper" className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="a4">A4</SelectItem>
              <SelectItem value="letter">Letter</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Separator />

        <Collapsible
          open={advanced}
          onOpenChange={setAdvanced}
          className="flex flex-col gap-5"
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="-mx-2.5 justify-between text-muted-foreground"
            >
              Advanced
              <ChevronDown
                className={
                  advanced
                    ? "rotate-180 transition-transform"
                    : "transition-transform"
                }
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="flex flex-col gap-5">
            <SliderField
              id="ribs"
              label="Ribs"
              value={params.ribs ?? resolved?.ribs ?? 6}
              min={1}
              max={20}
              step={1}
              display={
                params.ribs === null
                  ? `${resolved?.ribs ?? "…"} (auto)`
                  : String(params.ribs)
              }
              onChange={(v) => set({ ribs: v })}
            />
            <SliderField
              id="rings"
              label="Rings"
              value={params.rings ?? resolved?.rings ?? 2}
              min={0}
              max={6}
              step={1}
              display={
                params.rings === null
                  ? `${resolved?.rings ?? "…"} (auto)`
                  : String(params.rings)
              }
              onChange={(v) => set({ rings: v })}
            />
            <SwitchField
              id="stack"
              label="Stack ribs"
              description="Draw all ribs on one shared center line to save paper."
              checked={params.stack}
              onChange={(v) => set({ stack: v })}
            />
            <SwitchField
              id="features"
              label="Inner detail lines"
              description="Trace eyes, seams and other lines inside the outline."
              checked={params.features}
              onChange={(v) => set({ features: v })}
            />
            {boxy && (
              <SwitchField
                id="panels"
                label="Side panels"
                description="Add the outline again on each side, for flat-sided objects like cars. Print one and make two."
                checked={params.panels}
                onChange={(v) => set({ panels: v })}
              />
            )}
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}

function SliderField(props: {
  id: string;
  label: string;
  help?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display: string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <Label htmlFor={props.id} className="gap-1.5">
          {props.label}
          {props.help && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Info
                  className="size-3.5 text-muted-foreground"
                  aria-label={props.help}
                />
              </TooltipTrigger>
              <TooltipContent className="max-w-60">{props.help}</TooltipContent>
            </Tooltip>
          )}
        </Label>
        <span className="text-sm text-muted-foreground tabular-nums">
          {props.display}
        </span>
      </div>
      <Slider
        id={props.id}
        value={[props.value]}
        min={props.min}
        max={props.max}
        step={props.step}
        onValueChange={([v]) => props.onChange(v)}
        aria-label={props.label}
      />
    </div>
  );
}

function SwitchField(props: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex flex-col gap-1">
        <Label htmlFor={props.id}>{props.label}</Label>
        <p className="text-xs text-muted-foreground">{props.description}</p>
      </div>
      <Switch
        id={props.id}
        checked={props.checked}
        onCheckedChange={props.onChange}
      />
    </div>
  );
}
