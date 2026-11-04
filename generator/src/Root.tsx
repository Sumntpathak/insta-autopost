import React from "react";
import { Composition } from "remotion";
import postsJson from "../data/posts.json";
import type { Post } from "./lib/types";
import { SLIDES } from "./slides/Slides";
import { VIDEO } from "./theme";

const posts = postsJson as Post[];

type Props = { postId: string; slide: number };

const SlideRenderer: React.FC<Props> = ({ postId, slide }) => {
  const post = posts.find((p) => p.id === postId);
  if (!post) throw new Error(`post ${postId} not found in data/posts.json`);
  const Slide = SLIDES[slide];
  if (!Slide) throw new Error(`slide ${slide} out of range`);
  return <Slide post={post} />;
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Slide"
    component={SlideRenderer}
    durationInFrames={1}
    fps={VIDEO.fps}
    width={VIDEO.width}
    height={VIDEO.height}
    defaultProps={{ postId: posts[0]?.id ?? "S001", slide: 0 }}
  />
);
