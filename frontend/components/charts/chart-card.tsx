"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Line, LineChart } from "recharts";

import { Card, CardContent, CardHeader } from "@/components/ui/card";

type ChartCardProps = {
  title: string;
  description: string;
  data: Array<Record<string, string | number>>;
  xKey: string;
  yKey: string;
  type?: "bar" | "line";
};

export function ChartCard({ title, description, data, xKey, yKey, type = "bar" }: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <h3 className="text-base font-semibold text-foreground">{title}</h3>
        <p className="mt-1 text-sm text-muted">{description}</p>
      </CardHeader>
      <CardContent className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          {type === "bar" ? (
            <BarChart data={data}>
              <CartesianGrid stroke="#eaecf0" vertical={false} />
              <XAxis dataKey={xKey} tick={{ fill: "#667085", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#667085", fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey={yKey} fill="#2e6cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid stroke="#eaecf0" vertical={false} />
              <XAxis dataKey={xKey} tick={{ fill: "#667085", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#667085", fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Line type="monotone" dataKey={yKey} stroke="#2e6cf6" strokeWidth={3} dot={false} />
            </LineChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

