<template>
  <div
    class="farm-wheel"
    @mouseenter="stopAuto"
    @mouseleave="startAuto"
  >

    <!-- =========================
         3D 轮播舞台
    ========================== -->
    <div class="wheel-stage">

      <div
        v-for="(farm, index) in farms"
        :key="farm.id"
        class="farm-card"
        :class="{
          active: index === currentIndex,
          danger: farm.status === 'danger' || farm.status === 'offline',
          watering: farm.status === 'watering'
        }"
        :style="cardStyle(index)"
        @click="openMonitor(farm)"
      >

        <!-- =================================
             真实果园背景
        ================================== -->
        <div
          class="farm-background"
          :style="{
            backgroundImage: `url(${farm.background})`
          }"
        ></div>

        <!-- 背景遮罩 -->
        <div class="background-overlay"></div>

        <!-- =================================
             灌溉：细雨层
        ================================== -->
        <div
          v-if="farm.status === 'watering'"
          class="rain-layer"
          aria-hidden="true"
        >
          <span
            v-for="rain in rainDrops"
            :key="rain.id"
            class="rain-drop"
            :style="rain.style"
          ></span>
        </div>

        <!-- =================================
             灌溉：底部湿润水汽
        ================================== -->
        <div
          v-if="farm.status === 'watering'"
          class="water-mist"
          aria-hidden="true"
        >
          <span></span>
          <span></span>
          <span></span>
        </div>

        <!-- =================================
             卡片顶部状态标签
        ================================== -->
        <div class="status-badge">

          <span
            class="status-indicator"
            :class="{
              normal: farm.status === 'normal',
              danger: farm.status === 'danger' || farm.status === 'offline',
              watering: farm.status === 'watering'
            }"
          ></span>

          <span>
            {{ statusText(farm) }}
          </span>

        </div>


        <!-- =================================
             主信息区域
        ================================== -->
        <div class="farm-content">

          <!-- 果园名称 -->
          <div class="farm-heading">

            <div class="farm-type">
              FIELD MONITOR
            </div>

            <h2>
              <span class="tree-icon">🍊</span>
              {{ farm.name }}
            </h2>

          </div>


          <!-- =================================
               数据面板
          ================================== -->
          <div class="data-panel">

            <!-- 土壤湿度 -->
            <div class="data-block">

              <div class="data-label">
                SOIL MOISTURE
              </div>

              <div class="data-value">
                {{ farm.humidity }}
                <small>%</small>
              </div>

              <div class="data-line">
                <span
                  :style="{ width: `${Math.min(farm.humidity, 100)}%` }"
                ></span>
              </div>

            </div>


            <!-- 温度 -->
            <div class="data-block">

              <div class="data-label">
                AIR TEMPERATURE
              </div>

              <div class="data-value">
                {{ farm.temperature }}
                <small>℃</small>
              </div>

              <div class="temperature-state">
                环境温度
              </div>

            </div>

          </div>


          <!-- =================================
               底部状态
          ================================== -->
          <div class="bottom-info">

            <div class="status-text">

              <span
                class="status-dot"
                :class="{
                  normal: farm.status === 'normal',
                  danger: farm.status === 'danger' || farm.status === 'offline',
                  watering: farm.status === 'watering'
                }"
              ></span>

              <span>
                {{ statusText(farm) }}
              </span>

            </div>


            <div class="detail-link">

              <span>
                查看地块详情
              </span>

              <span class="detail-arrow">
                →
              </span>

            </div>

          </div>

        </div>


        <!-- =================================
             异常状态装饰
        ================================== -->
        <div
          v-if="farm.status === 'danger'"
          class="danger-glow"
        ></div>


        <!-- =================================
             灌溉状态装饰
        ================================== -->
        <div
          v-if="farm.status === 'watering'"
          class="watering-glow"
        ></div>

      </div>

    </div>


    <!-- =========================
         左箭头
    ========================== -->
    <button
      class="wheel-arrow wheel-arrow-left"
      type="button"
      aria-label="上一个果园"
      @click.stop="prev"
    >
      <span>‹</span>
    </button>


    <!-- =========================
         右箭头
    ========================== -->
    <button
      class="wheel-arrow wheel-arrow-right"
      type="button"
      aria-label="下一个果园"
      @click.stop="next"
    >
      <span>›</span>
    </button>


    <!-- =========================
         底部指示器
    ========================== -->
    <div class="wheel-indicator">

      <button
        v-for="(farm, index) in farms"
        :key="farm.id"
        type="button"
        class="indicator"
        :class="{
          active: index === currentIndex,
          danger: farm.status === 'danger' || farm.status === 'offline',
          watering: farm.status === 'watering'
        }"
        :aria-label="`查看${farm.name}`"
        @click.stop="goTo(index)"
      ></button>

    </div>

  </div>
</template>


<script setup>

import {
  computed,
  ref,
  watch,
  onMounted,
  onUnmounted
} from 'vue'

import {
  useRouter
} from 'vue-router'


/* =========================================================
   背景图片
========================================================= */

import { orangeCropBackground } from '@/utils/cropAssets'


/* =========================================================
   Router
========================================================= */

const router = useRouter()


const props = defineProps({
  plots: {
    type: Array,
    default: () => [],
  },
})

const farms = computed(() => props.plots.map((plot, index) => ({
  id: String(plot.plotId),
  name: plot.plotName,
  humidity: Number(plot.humidity ?? 0),
  temperature: Number(plot.temperature ?? 0),
  status: plot.irrigating || plot.status === 'irrigating'
    ? 'watering'
    : !plot.deviceOnline
      ? 'offline'
      : plot.status === 'alert'
        ? 'danger'
        : 'normal',
  background: orangeCropBackground(plot.cropName, index),
})))


/* =========================================================
   当前卡片
========================================================= */

const currentIndex = ref(0)

watch(farms, (items) => {
  if (currentIndex.value >= items.length) currentIndex.value = 0
}, { immediate: true })


/* =========================================================
   自动播放
========================================================= */

let timer = null

const AUTO_TIME = 3200


/* =========================================================
   雨滴
   ---------------------------------------------------------
   每个雨滴的位置、长度、速度、透明度略有不同，
   避免出现机械重复的 AI 特效感。
========================================================= */

const rainDrops = Array.from(
  { length: 68 },
  (_, index) => {

    const left =
      Math.random() * 100

    const height =
      14 + Math.random() * 20

    const duration =
      0.58 + Math.random() * 0.52

    const delay =
      Math.random() * 1.8

    const opacity =
      0.34 + Math.random() * 0.42

    const drift =
      7 + Math.random() * 11

    const width =
      index % 5 === 0 ? 2 : 1

    return {

      id: index,

      style: {

        left: `${left}%`,

        height: `${height}px`,

        opacity,

        animationDuration:
          `${duration}s`,

        animationDelay:
          `-${delay}s`,

        width: `${width}px`,

        '--rain-drift':
          `${drift}px`

      }

    }

  }
)


/* =========================================================
   下一张
========================================================= */

function next() {

  if (!farms.value.length) {
    return
  }

  currentIndex.value =
    (currentIndex.value + 1)
    % farms.value.length

}


/* =========================================================
   上一张
========================================================= */

function prev() {

  if (!farms.value.length) {
    return
  }

  currentIndex.value =
    (
      currentIndex.value -
      1 +
      farms.value.length
    )
    % farms.value.length

}


/* =========================================================
   跳转
========================================================= */

function goTo(index) {

  if (
    index < 0 ||
    index >= farms.value.length
  ) {

    return

  }

  currentIndex.value = index

}


/* =========================================================
   开始自动播放
========================================================= */

function startAuto() {

  stopAuto()

  if (farms.value.length <= 1) {
    return
  }

  timer = setInterval(() => {

    next()

  }, AUTO_TIME)

}


/* =========================================================
   停止自动播放
========================================================= */

function stopAuto() {

  if (timer) {

    clearInterval(timer)

    timer = null

  }

}


/* =========================================================
   3D 卡片位置
========================================================= */

function cardStyle(index) {

  const total =
    farms.value.length

  if (!total) {
    return {}
  }


  let offset =
    index -
    currentIndex.value


  /* 环形排列 */

  if (offset > total / 2) {

    offset -= total

  }

  if (offset < -total / 2) {

    offset += total

  }


  /* =========================================
     超出范围
  ========================================= */

  const maxDistance = 2

  if (
    Math.abs(offset) >
    maxDistance
  ) {

    return {

      opacity: 0,

      pointerEvents: 'none',

      transform: `
        translateX(${offset * 420}px)
        translateZ(-650px)
        rotateY(${offset > 0 ? -58 : 58}deg)
        scale(.42)
      `,

      filter: 'blur(6px)',

      zIndex: 0

    }

  }


  /* =========================================
     左右距离
  ========================================= */

  const x =
    offset * 430


  /* =========================================
     景深
  ========================================= */

  let z = -280

  if (offset === 0) {

    z = 180

  } else if (
    Math.abs(offset) === 1
  ) {

    z = -35

  } else {

    z = -300

  }


  /* =========================================
     缩放
  ========================================= */

  let scale = .54

  if (offset === 0) {

    scale = 1

  } else if (
    Math.abs(offset) === 1
  ) {

    scale = .72

  }


  /* =========================================
     Y轴旋转
  ========================================= */

  const rotateY =
    offset * -21


  /* =========================================
     透明度
  ========================================= */

  let opacity = .12

  if (offset === 0) {

    opacity = 1

  } else if (
    Math.abs(offset) === 1
  ) {

    opacity = .52

  }


  /* =========================================
     景深模糊
  ========================================= */

  let blur = 0

  if (
    Math.abs(offset) === 1
  ) {

    blur = .7

  } else if (
    Math.abs(offset) === 2
  ) {

    blur = 3

  }


  return {

    transform: `
      translateX(${x}px)
      translateZ(${z}px)
      rotateY(${rotateY}deg)
      scale(${scale})
    `,

    opacity,

    filter:
      `blur(${blur}px)`,

    zIndex:
      100 -
      Math.abs(offset) * 10,

    pointerEvents:
      Math.abs(offset) <= 1
        ? 'auto'
        : 'none'

  }

}


/* =========================================================
   点击进入详情
========================================================= */

function openMonitor(farm) {

  router.push({

    name: 'farmer-management',

    query: {

      plotId:
        String(farm.id)

    }

  })

}


/* =========================================================
   状态文字
========================================================= */

function statusText(farm) {

  if (
    farm.status === 'offline'
  ) {

    return '暂未接入设备'

  }

  if (
    farm.status === 'danger'
  ) {

    return '湿度异常'

  }

  if (
    farm.status === 'watering'
  ) {

    return '灌溉进行中'

  }

  return '状态正常'

}


/* =========================================================
   生命周期
========================================================= */

onMounted(() => {

  startAuto()

})


onUnmounted(() => {

  stopAuto()

})

</script>


<style scoped>

/* =========================================================
   整体区域
========================================================= */

.farm-wheel {

  position: relative;

  width: 100%;

  height: 480px;

  display: flex;

  align-items: center;

  justify-content: center;

  overflow: hidden;

  perspective: 1500px;

}


/* =========================================================
   舞台
========================================================= */

.wheel-stage {

  position: relative;

  width: 100%;

  height: 470px;

  display: flex;

  align-items: center;

  justify-content: center;

  transform-style: preserve-3d;

}


/* =========================================================
   卡片
========================================================= */

.farm-card {

  position: absolute;

  left: 50%;

  top: 50%;

  width: 720px;

  height: 410px;

  margin-left: -360px;

  margin-top: -205px;

  overflow: hidden;

  border-radius: 28px;

  cursor: pointer;

  transform-style: preserve-3d;

  backface-visibility: hidden;

  border: 1px solid
    rgba(255,255,255,.55);

  background: #4a2b18;

  box-shadow:
    0 30px 70px
    rgba(82,43,16,.25);

  transition:
    transform 1.25s
      cubic-bezier(.22,.61,.36,1),
    opacity 1.1s ease,
    filter 1.1s ease,
    box-shadow .6s ease;

  will-change:
    transform,
    opacity;

}


/* =========================================================
   当前卡片
========================================================= */

.farm-card.active {

  box-shadow:
    0 42px 110px
      rgba(99,50,16,.32),
    0 10px 30px
      rgba(0,0,0,.12);

}


/* =========================================================
   背景图片
========================================================= */

.farm-background {

  position: absolute;

  inset: 0;

  z-index: 0;

  background-position: center;

  background-size: cover;

  background-repeat: no-repeat;

  transform: scale(1.04);

  transition:
    transform 1.5s ease;

}


/* 正面卡片图片略微放大 */

.farm-card.active
.farm-background {

  transform:
    scale(1.08);

}


/* =========================================================
   图片遮罩
========================================================= */

.background-overlay {

  position: absolute;

  inset: 0;

  z-index: 1;

  background:
    linear-gradient(
      90deg,
      rgba(54,27,12,.88) 0%,
      rgba(75,37,14,.72) 35%,
      rgba(88,45,18,.38) 68%,
      rgba(48,24,10,.20) 100%
    );

}


/* =========================================================
   右侧图片柔光
========================================================= */

.background-overlay::after {

  content: '';

  position: absolute;

  inset: 0;

  background:
    linear-gradient(
      180deg,
      rgba(255,255,255,.08),
      transparent 35%,
      rgba(0,0,0,.18)
    );

}


/* =========================================================
   主内容
========================================================= */

.farm-content {

  position: relative;

  z-index: 5;

  width: 100%;

  height: 100%;

  box-sizing: border-box;

  padding:
    42px 48px 38px;

  color: white;

}


/* =========================================================
   顶部状态
========================================================= */

.status-badge {

  position: absolute;

  top: 30px;

  right: 34px;

  display: flex;

  align-items: center;

  gap: 8px;

  padding:
    8px 13px;

  border-radius: 999px;

  background:
    rgba(255,255,255,.13);

  border:
    1px solid
    rgba(255,255,255,.18);

  backdrop-filter:
    blur(12px);

  -webkit-backdrop-filter:
    blur(12px);

  color:
    rgba(255,255,255,.92);

  font-size: 13px;

  font-weight: 600;

}


/* =========================================================
   状态灯
========================================================= */

.status-indicator {

  width: 7px;

  height: 7px;

  border-radius: 50%;

}


.status-indicator.normal {

  background: #8dcc61;

  box-shadow:
    0 0 0 4px
    rgba(141,204,97,.13);

}


.status-indicator.danger {

  background: #f06b5e;

  box-shadow:
    0 0 0 4px
    rgba(240,107,94,.14);

}


.status-indicator.watering {

  background: #72c8e8;

  box-shadow:
    0 0 0 4px
    rgba(114,200,232,.14);

}


/* =========================================================
   标题
========================================================= */

.farm-heading {

  margin-top: 10px;

}


.farm-type {

  margin-bottom: 8px;

  color:
    rgba(255,255,255,.55);

  font-size: 11px;

  font-weight: 700;

  letter-spacing: 2.5px;

}


.farm-heading h2 {

  display: flex;

  align-items: center;

  gap: 12px;

  margin: 0;

  color: white;

  font-size: 39px;

  font-weight: 750;

  letter-spacing: .5px;

  text-shadow:
    0 2px 12px
    rgba(0,0,0,.18);

}


.tree-icon {

  font-size: 34px;

}


/* =========================================================
   数据面板
========================================================= */

.data-panel {

  position: absolute;

  left: 48px;

  right: 48px;

  bottom: 112px;

  display: grid;

  grid-template-columns:
    1fr 1fr;

  gap: 20px;

}


/* =========================================================
   数据块
========================================================= */

.data-block {

  padding:
    18px 20px;

  border:
    1px solid
    rgba(255,255,255,.14);

  border-radius: 16px;

  background:
    rgba(48,23,8,.34);

  backdrop-filter:
    blur(10px);

  -webkit-backdrop-filter:
    blur(10px);

}


/* =========================================================
   数据标签
========================================================= */

.data-label {

  color:
    rgba(255,255,255,.58);

  font-size: 11px;

  font-weight: 700;

  letter-spacing: 1.6px;

}


/* =========================================================
   数据数字
========================================================= */

.data-value {

  margin-top: 5px;

  color: white;

  font-size: 43px;

  font-weight: 750;

  line-height: 1;

}


.data-value small {

  margin-left: 3px;

  color:
    rgba(255,255,255,.72);

  font-size: 19px;

  font-weight: 500;

}


/* =========================================================
   湿度进度线
========================================================= */

.data-line {

  height: 3px;

  margin-top: 13px;

  overflow: hidden;

  border-radius: 5px;

  background:
    rgba(255,255,255,.12);

}


.data-line span {

  display: block;

  height: 100%;

  border-radius: inherit;

  background:
    rgba(245,165,63,.92);

  box-shadow:
    0 0 8px
    rgba(245,150,39,.36);

}


/* =========================================================
   温度说明
========================================================= */

.temperature-state {

  margin-top: 10px;

  color:
    rgba(255,255,255,.46);

  font-size: 12px;

}


/* =========================================================
   底部
========================================================= */

.bottom-info {

  position: absolute;

  left: 48px;

  right: 48px;

  bottom: 36px;

  display: flex;

  align-items: center;

  justify-content: space-between;

}


/* =========================================================
   状态文字
========================================================= */

.status-text {

  display: flex;

  align-items: center;

  gap: 9px;

  color:
    rgba(255,255,255,.88);

  font-size: 15px;

  font-weight: 650;

}


.status-dot {

  width: 8px;

  height: 8px;

  border-radius: 50%;

}


.status-dot.normal {

  background: #8fc96a;

}


.status-dot.danger {

  background: #ef695d;

}


.status-dot.watering {

  background: #73c8e6;

  animation:
    wateringPulse
    1.4s ease-in-out
    infinite;

}


@keyframes wateringPulse {

  0%,
  100% {

    opacity: .55;

    box-shadow:
      0 0 0
      rgba(115,200,230,0);

  }

  50% {

    opacity: 1;

    box-shadow:
      0 0 12px
      rgba(115,200,230,.65);

  }

}


/* =========================================================
   详情链接
========================================================= */

.detail-link {

  display: flex;

  align-items: center;

  gap: 9px;

  color:
    rgba(255,255,255,.65);

  font-size: 13px;

  transition:
    color .3s ease,
    transform .3s ease;

}


.detail-arrow {

  font-size: 20px;

  line-height: 1;

}


.farm-card.active:hover
.detail-link {

  color: white;

  transform:
    translateX(4px);

}


/* =========================================================
   灌溉雨层
========================================================= */

.rain-layer {

  position: absolute;

  inset: 0;

  z-index: 4;

  overflow: hidden;

  pointer-events: none;

  opacity: .92;

  background:
    linear-gradient(
      180deg,
      rgba(124, 206, 235, .08),
      transparent 42%,
      rgba(96, 186, 218, .06)
    );

  mix-blend-mode: screen;

}


/* =========================================================
   单根雨丝
========================================================= */

.rain-drop {

  position: absolute;

  top: -30px;

  min-width: 1px;

  border-radius: 999px;

  background:
    linear-gradient(
      180deg,
      rgba(225,246,255,0),
      rgba(222,247,255,.98)
    );

  box-shadow:
    0 0 3px
    rgba(157, 222, 244, .38);

  transform:
    rotate(14deg);

  animation:
    rainFall
    linear
    infinite;

}


.rain-drop:nth-child(3n) {

  filter: blur(.35px);

}


.rain-drop:nth-child(5n) {

  box-shadow:
    0 0 5px
    rgba(180, 234, 251, .58);

}


@keyframes rainFall {

  0% {

    transform:
      translate3d(
        0,
        -30px,
        0
      )
      rotate(14deg);

  }

  100% {

    transform:
      translate3d(
        var(--rain-drift),
        470px,
        0
      )
      rotate(14deg);

  }

}


/* =========================================================
   灌溉水雾
========================================================= */

.water-mist {

  position: absolute;

  left: -5%;

  right: -5%;

  bottom: -20px;

  height: 100px;

  z-index: 4;

  pointer-events: none;

  opacity: .7;

  overflow: hidden;

}


.water-mist span {

  position: absolute;

  bottom: -30px;

  width: 220px;

  height: 70px;

  border-radius: 50%;

  background:
    rgba(214,242,248,.12);

  filter:
    blur(15px);

  animation:
    mistMove
    5s ease-in-out
    infinite;

}


.water-mist span:nth-child(1) {

  left: 8%;

  animation-delay: 0s;

}


.water-mist span:nth-child(2) {

  left: 42%;

  animation-delay: -2s;

}


.water-mist span:nth-child(3) {

  right: 2%;

  animation-delay: -3.5s;

}


@keyframes mistMove {

  0%,
  100% {

    transform:
      translateX(-20px)
      scale(.9);

    opacity: .25;

  }

  50% {

    transform:
      translateX(35px)
      scale(1.08);

    opacity: .6;

  }

}


/* =========================================================
   灌溉氛围
========================================================= */

.watering-glow {

  position: absolute;

  inset: 0;

  z-index: 2;

  pointer-events: none;

  background:
    linear-gradient(
      180deg,
      rgba(99,175,198,.08),
      transparent 45%,
      rgba(90,171,196,.10)
    );

}


/* =========================================================
   异常氛围
========================================================= */

.danger-glow {

  position: absolute;

  left: 0;

  top: 0;

  bottom: 0;

  width: 10px;

  z-index: 6;

  background:
    linear-gradient(
      180deg,
      rgba(245,103,91,.2),
      rgba(245,103,91,.9),
      rgba(245,103,91,.2)
    );

  box-shadow:
    0 0 18px
    rgba(245,103,91,.28);

}



/* =========================================================
   异常数据线
========================================================= */

.farm-card.danger
.data-line span {

  background:
    #e36a5d;

  box-shadow:
    0 0 8px
    rgba(227,106,93,.35);

}


/* =========================================================
   灌溉数据线
========================================================= */

.farm-card.watering
.data-line span {

  background:
    #72bdd8;

  box-shadow:
    0 0 8px
    rgba(114,189,216,.32);

}


/* =========================================================
   左右按钮
========================================================= */

.wheel-arrow {

  position: absolute;

  top: 50%;

  width: 58px;

  height: 58px;

  padding: 0;

  margin: 0;

  transform:
    translateY(-50%);

  display: flex;

  align-items: center;

  justify-content: center;

  z-index: 500;

  border:
    1px solid
    rgba(58,91,65,.18);

  border-radius: 50%;

  background:
    rgba(255,255,255,.84);

  backdrop-filter:
    blur(14px);

  -webkit-backdrop-filter:
    blur(14px);

  box-shadow:
    0 12px 34px
    rgba(29,55,36,.15);

  color:
    #416a4b;

  cursor: pointer;

  transition:
    transform .28s ease,
    background .28s ease,
    box-shadow .28s ease;

}


.wheel-arrow span {

  margin-top: -5px;

  font-family:
    Arial,
    sans-serif;

  font-size: 42px;

  font-weight: 300;

  line-height: 1;

}


.wheel-arrow-left {

  left: 28px;

}


.wheel-arrow-right {

  right: 28px;

}


.wheel-arrow:hover {

  background:
    rgba(255,255,255,.97);

  box-shadow:
    0 18px 42px
    rgba(29,55,36,.22);

}


.wheel-arrow-left:hover {

  transform:
    translateY(-50%)
    translateX(-4px);

}


.wheel-arrow-right:hover {

  transform:
    translateY(-50%)
    translateX(4px);

}


.wheel-arrow:active {

  transform:
    translateY(-50%)
    scale(.91);

}


/* =========================================================
   底部指示器
========================================================= */

.wheel-indicator {

  position: absolute;

  left: 50%;

  bottom: 18px;

  transform:
    translateX(-50%);

  display: flex;

  align-items: center;

  gap: 8px;

  z-index: 600;

}


.indicator {

  width: 7px;

  height: 7px;

  padding: 0;

  border: 0;

  border-radius: 10px;

  background:
    rgba(157,91,38,.28);

  cursor: pointer;

  transition:
    width .3s ease,
    background .3s ease,
    box-shadow .3s ease;

}


.indicator.active {

  width: 27px;

  background:
    #e47a20;

  box-shadow:
    0 3px 10px
    rgba(228,122,32,.26);

}


.indicator.danger {

  background:
    rgba(220,88,76,.5);

}


.indicator.watering {

  background:
    rgba(77,164,194,.5);

}


.indicator.danger.active {

  background:
    #d75d51;

}


.indicator.watering.active {

  background:
    #5aa8c5;

}


/* =========================================================
   平板
========================================================= */

@media (max-width: 1200px) {

  .farm-card {

    width: 620px;

    margin-left: -310px;

  }


  .farm-heading h2 {

    font-size: 34px;

  }


  .data-value {

    font-size: 38px;

  }


  .wheel-arrow-left {

    left: 18px;

  }


  .wheel-arrow-right {

    right: 18px;

  }

}


/* =========================================================
   小屏
========================================================= */

@media (max-width: 850px) {

  .farm-wheel {

    height: 520px;

  }


  .farm-card {

    width: 500px;

    height: 350px;

    margin-left: -250px;

    margin-top: -175px;

    border-radius: 24px;

  }


  .farm-content {

    padding:
      32px 34px 30px;

  }


  .farm-heading h2 {

    font-size: 29px;

  }


  .farm-type {

    font-size: 9px;

  }


  .data-panel {

    left: 34px;

    right: 34px;

    bottom: 92px;

  }


  .data-block {

    padding:
      14px 15px;

  }


  .data-value {

    font-size: 31px;

  }


  .bottom-info {

    left: 34px;

    right: 34px;

    bottom: 28px;

  }


  .wheel-arrow {

    width: 50px;

    height: 50px;

  }


  .wheel-arrow-left {

    left: 8px;

  }


  .wheel-arrow-right {

    right: 8px;

  }

}


/* =========================================================
   手机
========================================================= */

@media (max-width: 600px) {

  .farm-wheel {

    height: 440px;

  }


  .farm-card {

    width: 390px;

    height: 300px;

    margin-left: -195px;

    margin-top: -150px;

  }


  .farm-content {

    padding:
      25px 25px 24px;

  }


  .status-badge {

    top: 20px;

    right: 20px;

    padding:
      6px 9px;

    font-size: 11px;

  }


  .farm-heading h2 {

    font-size: 24px;

  }


  .tree-icon {

    font-size: 26px;

  }


  .data-panel {

    left: 25px;

    right: 25px;

    bottom: 78px;

    gap: 10px;

  }


  .data-block {

    padding:
      11px 12px;

    border-radius: 12px;

  }


  .data-label {

    font-size: 8px;

  }


  .data-value {

    font-size: 25px;

  }


  .data-value small {

    font-size: 13px;

  }


  .bottom-info {

    left: 25px;

    right: 25px;

    bottom: 22px;

  }


  .status-text {

    font-size: 12px;

  }


  .detail-link {

    font-size: 10px;

  }


  .wheel-arrow {

    width: 42px;

    height: 42px;

  }


  .wheel-arrow span {

    font-size: 30px;

  }


  .wheel-indicator {

    bottom: 8px;

  }

}

</style>
