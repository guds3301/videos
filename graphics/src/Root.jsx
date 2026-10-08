import React from 'react';
import {Composition} from 'remotion';
import {ChapterTitle} from './ChapterTitle.jsx';
import {MeasureLine} from './MeasureLine.jsx';
import {ComponentDiagram} from './ComponentDiagram.jsx';

// Every composition takes its duration and frame rate from props so one spec file
// (id, composition, duration_frames, fps, props) fully describes a clip.
const meta = ({props}) => ({
  durationInFrames: props.duration_frames ?? 120,
  fps: props.fps ?? 24,
  width: props.width ?? 1920,
  height: props.height ?? 1080,
});

const common = {width: 1920, height: 1080, fps: 24, durationInFrames: 120, calculateMetadata: meta};

export const RemotionRoot = () => (
  <>
    <Composition id="ChapterTitle" component={ChapterTitle} {...common} defaultProps={{number: '01', title: 'CHAPTER TITLE'}} />
    <Composition id="MeasureLine" component={MeasureLine} {...common} defaultProps={{}} />
    <Composition id="ComponentDiagram" component={ComponentDiagram} {...common} defaultProps={{}} />
  </>
);
