<script lang="ts">
	import { onMount } from 'svelte';

	// The globe is drawn by one fragment shader (sphere, dotted continents, rim and halo)
	// with a 2D canvas on top for the floating data packets. The view is a camera raised
	// TILT radians above the equator, spinning eastward so the continents drift to the right.
	const TILT = 0.42;
	const SPIN_SPEED = 0.05;
	const START_LON = 0.35;
	const INTRO_MS = 2400;
	// Globe centre and radius as fractions of the scene box.
	const CX = 0.5;
	const CY = 0.5;
	const RADIUS = 0.36;

	let scene: HTMLDivElement;
	let gl_canvas: HTMLCanvasElement;
	let fx_canvas: HTMLCanvasElement;
	let fallback = $state(false);
	let ready = $state(false);

	const VERT = `#version 300 es
in vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }`;

	const FRAG = `#version 300 es
precision highp float;
uniform vec2 u_res;
uniform vec2 u_center;
uniform float u_radius;
uniform float u_time;
uniform float u_spin;
uniform float u_tilt;
uniform float u_intro;
uniform float u_step;
uniform sampler2D u_land;
out vec4 o;
const float PI = 3.14159265;

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void main() {
	vec2 frag = vec2(gl_FragCoord.x, u_res.y - gl_FragCoord.y);
	vec2 p = (frag - u_center) / u_radius;
	p.y = -p.y;
	float r = length(p);
	float px = 1.0 / u_radius;
	// 1 on the lit lower-left limb, 0 on the far upper-right.
	float side = 0.5 + 0.5 * dot(r > 0.0 ? p / r : vec2(0.0), normalize(vec2(-0.72, -0.6)));
	float glowIn = smoothstep(0.0, 1.0, u_intro);

	// Atmosphere outside the disc: a tight bright band and a wide soft bloom.
	float d = max(r - 1.0, 0.0);
	float tight = exp(-d * 16.0);
	float wide = exp(-d * 4.2);
	vec3 halo = vec3(0.16, 0.5, 1.0) * tight * (0.35 + 1.15 * side)
		+ vec3(0.07, 0.24, 0.62) * wide * (0.25 + 0.75 * side)
		+ vec3(0.5, 0.82, 1.0) * exp(-d * 60.0) * (0.15 + 1.0 * side);
	// Fade to nothing before the canvas edge so the bloom never shows a seam.
	vec2 edge = abs(frag / u_res - 0.5) * 2.0;
	halo *= glowIn * (1.0 - smoothstep(0.72, 1.0, length(edge)));
	float haloA = clamp(max(max(halo.r, halo.g), halo.b), 0.0, 1.0);

	vec3 col = vec3(0.0);
	if (r < 1.0) {
		float z = sqrt(1.0 - r * r);
		vec3 n = vec3(p, z);
		float ct = cos(u_tilt), st = sin(u_tilt);
		vec3 w = vec3(n.x, ct * n.y + st * n.z, -st * n.y + ct * n.z);
		float cs = cos(u_spin), ss = sin(u_spin);
		w = vec3(cs * w.x + ss * w.z, w.y, -ss * w.x + cs * w.z);
		float lat = asin(clamp(w.y, -1.0, 1.0));
		float lon = atan(w.x, w.z);

		// Dots sit on latitude rows; each row holds as many dots as fit its circumference.
		float row = floor((lat + PI * 0.5) / u_step);
		float latc = (row + 0.5) * u_step - PI * 0.5;
		float count = max(1.0, floor(2.0 * PI * cos(latc) / u_step));
		float lstep = 2.0 * PI / count;
		float ci = floor((lon + PI) / lstep);
		float lonc = (ci + 0.5) * lstep - PI;
		vec2 q = vec2((lon - lonc) * cos(latc), lat - latc) / u_step;
		vec2 uv = vec2((lonc + PI) / (2.0 * PI), 0.5 - latc / PI);
		float land = smoothstep(0.3, 0.7, texture(u_land, uv).r);

		float h = hash(vec2(row, ci));
		float h2 = hash(vec2(ci + 17.0, row * 1.7));
		float half_ = mix(0.12, 0.27, land);
		float rad = half_ * 0.42;
		vec2 aq = abs(q) - (half_ - rad);
		float sd = length(max(aq, 0.0)) + min(max(aq.x, aq.y), 0.0) - rad;
		float fw = fwidth(sd) + 1e-4;
		float dotMask = 1.0 - smoothstep(-fw, fw, sd);
		// Dots materialise in a random order during the intro.
		dotMask *= smoothstep(h, h + 0.18, u_intro * 1.2);

		float tw = 0.5 + 0.5 * sin(u_time * (0.6 + h * 1.9) + h * 62.83);
		float wave = 0.5 + 0.5 * sin(lat * 7.0 + lon * 3.0 - u_time * 0.9);
		float hot = step(0.955, h2) * (0.55 + 0.45 * sin(u_time * (1.6 + h * 2.0) + h2 * 90.0));
		vec3 landCol = mix(vec3(0.2, 0.52, 1.0), vec3(0.85, 0.95, 1.0), hot);
		float landI = (0.4 + 0.3 * tw) * (0.75 + 0.5 * wave) * (1.0 + 1.8 * hot);
		vec3 seaCol = vec3(0.16, 0.38, 0.85);
		float seaI = 0.24 * (0.7 + 0.3 * tw);
		// Land dots bleed a little light into their cell.
		float bloom = land * exp(-max(sd, 0.0) * 9.0) * 0.22 * (0.6 + 0.4 * tw) * (1.0 + hot * 1.5);

		vec3 L = normalize(vec3(-0.55, -0.62, 0.56));
		float diff = max(dot(n, L), 0.0);
		float lower = smoothstep(0.35, -1.0, p.y);
		float shade = 0.3 + 0.85 * diff + 0.5 * lower;

		vec3 body = mix(vec3(0.006, 0.02, 0.06), vec3(0.03, 0.14, 0.36), clamp(diff * 0.75 + lower * 0.55, 0.0, 1.0));
		body += vec3(0.02, 0.07, 0.18) * pow(1.0 - z, 1.5);

		float vis = smoothstep(0.0, 0.22, z);
		float appear = smoothstep(h, h + 0.18, u_intro * 1.2);
		col = body + dotMask * vis * shade * (land * landCol * landI + (1.0 - land) * seaCol * seaI);
		col += landCol * bloom * vis * shade * appear;

		// Rim light: fresnel, strongest on the side facing the stage light.
		float fres = pow(1.0 - z, 3.0);
		col += fres * mix(vec3(0.1, 0.38, 1.0), vec3(0.5, 0.85, 1.0), side) * (0.3 + 1.9 * side) * glowIn;
		col += vec3(0.1, 0.4, 1.0) * exp(-(1.0 - r) * 22.0) * side * 0.7 * glowIn;
	}

	float inside = 1.0 - smoothstep(1.0 - px, 1.0 + px, r);
	// A crisp bright limb line.
	float lx = (r - 1.0) / (1.6 * px);
	vec3 limb = vec3(0.42, 0.78, 1.0) * exp(-lx * lx) * (0.25 + 1.3 * side) * glowIn;
	vec3 rgb = mix(halo, col, inside) + limb;
	// Clamp without shifting hue, letting the brightest light bloom towards white.
	float peak = max(rgb.r, max(rgb.g, rgb.b));
	if (peak > 1.0) rgb = mix(rgb / peak, vec3(1.0), clamp((peak - 1.0) * 0.3, 0.0, 0.45));
	// Keep the output validly premultiplied: alpha must cover every channel.
	float a = max(max(inside, haloA), max(rgb.r, max(rgb.g, rgb.b)));
	o = vec4(rgb, clamp(a, 0.0, 1.0));
}`;

	type Packet = {
		lat: number;
		lon: number;
		alt: number;
		size: number;
		born: number;
		life: number;
		blur: boolean;
		phase: number;
		dot: boolean;
	};

	function compile(gl: WebGL2RenderingContext, type: number, src: string) {
		const s = gl.createShader(type)!;
		gl.shaderSource(s, src);
		gl.compileShader(s);
		if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) ?? 'shader');
		return s;
	}

	// One glowing hollow rounded rectangle, drawn once and stamped for every packet.
	function sprite(blur: boolean) {
		const c = document.createElement('canvas');
		const w = 96;
		const h = 128;
		c.width = w;
		c.height = h;
		const ctx = c.getContext('2d')!;
		const bw = 30;
		const bh = 46;
		const x = (w - bw) / 2;
		const y = (h - bh) / 2;
		ctx.shadowColor = blur ? 'rgba(110,180,255,0.9)' : 'rgba(120,190,255,1)';
		ctx.shadowBlur = blur ? 26 : 16;
		ctx.lineWidth = blur ? 9 : 6;
		ctx.strokeStyle = blur ? 'rgba(170,215,255,0.55)' : 'rgba(225,242,255,1)';
		ctx.fillStyle = blur ? 'rgba(90,160,255,0.18)' : 'rgba(70,140,255,0.22)';
		ctx.beginPath();
		ctx.roundRect(x, y, bw, bh, 9);
		ctx.fill();
		ctx.stroke();
		if (!blur) {
			ctx.shadowBlur = 0;
			ctx.lineWidth = 2.5;
			ctx.strokeStyle = 'rgba(255,255,255,0.95)';
			ctx.stroke();
		}
		return c;
	}

	function sparkSprite() {
		const c = document.createElement('canvas');
		c.width = c.height = 48;
		const ctx = c.getContext('2d')!;
		ctx.shadowColor = 'rgba(130,200,255,1)';
		ctx.shadowBlur = 12;
		ctx.fillStyle = 'rgba(235,246,255,1)';
		ctx.beginPath();
		ctx.roundRect(18, 18, 12, 12, 3);
		ctx.fill();
		return c;
	}

	onMount(() => {
		const gl = gl_canvas.getContext('webgl2', { premultipliedAlpha: true, antialias: false, alpha: true });
		const fx = fx_canvas.getContext('2d');
		if (!gl || !fx) {
			fallback = true;
			return;
		}

		let prog: WebGLProgram;
		try {
			prog = gl.createProgram()!;
			gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VERT));
			gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FRAG));
			gl.linkProgram(prog);
			if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog) ?? 'link');
		} catch (e) {
			console.warn('Globe: falling back to the still image', e);
			fallback = true;
			return;
		}
		gl.useProgram(prog);
		const buf = gl.createBuffer();
		gl.bindBuffer(gl.ARRAY_BUFFER, buf);
		gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
		const loc = gl.getAttribLocation(prog, 'a_pos');
		gl.enableVertexAttribArray(loc);
		gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
		const u = (name: string) => gl.getUniformLocation(prog, name);
		const U = {
			res: u('u_res'),
			center: u('u_center'),
			radius: u('u_radius'),
			time: u('u_time'),
			spin: u('u_spin'),
			tilt: u('u_tilt'),
			intro: u('u_intro'),
			step: u('u_step'),
			land: u('u_land')
		};

		const tex = gl.createTexture();
		gl.bindTexture(gl.TEXTURE_2D, tex);
		gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
		gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
		gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
		gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
		gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
		gl.uniform1i(U.land, 0);

		const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
		const reduced = () => motionQuery.matches || document.documentElement.dataset.motion === 'reduce';

		const sharp = sprite(false);
		const soft = sprite(true);
		const spark = sparkSprite();
		let packets: Packet[] = [];

		let width = 0;
		let height = 0;
		let dpr = 1;
		let radius = 0;
		let start = 0;
		let frozen = 0;
		let raf = 0;
		let visible = true;
		let loaded = false;

		const rand = (a: number, b: number) => a + Math.random() * (b - a);

		// Spawn on the visible upper part of the globe, then let it ride the rotation.
		function spawn(now: number, settled = false): Packet {
			const dot = Math.random() < 0.35;
			const blur = !dot && Math.random() < 0.16;
			let x: number;
			let y: number;
			do {
				x = rand(-0.95, 0.95);
				y = rand(-0.35, 0.98);
			} while (x * x + y * y > 0.92);
			const z = Math.sqrt(1 - x * x - y * y);
			const ct = Math.cos(TILT);
			const st = Math.sin(TILT);
			const wy = ct * y + st * z;
			const wz = -st * y + ct * z;
			const spin = spinAt(now);
			const cs = Math.cos(spin);
			const ss = Math.sin(spin);
			const wx = cs * x + ss * wz;
			const wz2 = -ss * x + cs * wz;
			return {
				lat: Math.asin(Math.max(-1, Math.min(1, wy))),
				lon: Math.atan2(wx, wz2),
				alt: blur ? rand(1.12, 1.3) : rand(1.0, 1.1),
				size: dot ? rand(0.6, 1.1) : blur ? rand(1.8, 2.8) : rand(0.75, 1.45),
				born: settled ? now - rand(0, 3000) : now + rand(0, 2600),
				life: rand(2600, 6200),
				blur,
				phase: rand(0, Math.PI * 2),
				dot
			};
		}

		function spinAt(t: number) {
			return START_LON - (t / 1000) * SPIN_SPEED;
		}

		function project(p: Packet, spin: number) {
			const cl = Math.cos(p.lat);
			let x = cl * Math.sin(p.lon);
			const y = Math.sin(p.lat);
			let z = cl * Math.cos(p.lon);
			const cs = Math.cos(spin);
			const ss = Math.sin(spin);
			const x2 = cs * x - ss * z;
			z = ss * x + cs * z;
			x = x2;
			const ct = Math.cos(TILT);
			const st = Math.sin(TILT);
			const vy = ct * y - st * z;
			const vz = st * y + ct * z;
			return { x: x * p.alt, y: vy * p.alt, z: vz };
		}

		function resize() {
			const rect = scene.getBoundingClientRect();
			// Keep the backing store within a sane pixel budget on very large screens.
			dpr = Math.min(2, window.devicePixelRatio || 1, 2600 / Math.max(1, rect.width));
			width = Math.max(1, Math.round(rect.width * dpr));
			height = Math.max(1, Math.round(rect.height * dpr));
			for (const c of [gl_canvas, fx_canvas]) {
				c.width = width;
				c.height = height;
			}
			radius = Math.min(width, height) * RADIUS;
			gl!.viewport(0, 0, width, height);
			const count = Math.round(Math.min(70, Math.max(26, (rect.width * rect.height) / 13000)));
			const now = performance.now() - start;
			packets = Array.from({ length: count }, () => spawn(now, reduced() || now > INTRO_MS));
		}

		function draw(t: number) {
			const intro = reduced() ? 1 : Math.min(1, t / INTRO_MS);
			const ease = 1 - Math.pow(1 - intro, 3);
			const r = radius * (0.93 + 0.07 * ease);
			const spin = spinAt(t);
			const cx = width * CX;
			const cy = height * CY;
			// About six CSS pixels between dots at the centre of the disc.
			const step = Math.min(0.022, Math.max(0.0075, (6 * dpr) / r));

			gl!.uniform2f(U.res, width, height);
			gl!.uniform2f(U.center, cx, cy);
			gl!.uniform1f(U.radius, r);
			gl!.uniform1f(U.time, t / 1000);
			gl!.uniform1f(U.spin, spin);
			gl!.uniform1f(U.tilt, TILT);
			gl!.uniform1f(U.intro, ease);
			gl!.uniform1f(U.step, step);
			gl!.clearColor(0, 0, 0, 0);
			gl!.clear(gl!.COLOR_BUFFER_BIT);
			gl!.drawArrays(gl!.TRIANGLES, 0, 3);

			fx!.clearRect(0, 0, width, height);
			fx!.globalCompositeOperation = 'lighter';
			const unit = r / 420;
			const still = reduced();
			for (let i = 0; i < packets.length; i++) {
				const p = packets[i];
				const age = t - p.born;
				if (!still && age > p.life) {
					packets[i] = spawn(t);
					continue;
				}
				if (!still && age < 0) continue;
				const v = project(p, spin);
				const outside = v.x * v.x + v.y * v.y > 1;
				if (v.z < 0 && !outside) continue;
				let a = still ? 0.85 : Math.min(1, age / 500) * Math.min(1, (p.life - age) / 700);
				// Freshly spawned packets blink on, like data arriving.
				if (!still && age < 420) a *= age % 140 < 80 ? 1 : 0.25;
				a *= 0.78 + 0.22 * Math.sin(t / 260 + p.phase);
				a *= Math.min(1, Math.max(0, v.z * 4 + (outside ? 1 : 0)));
				a *= ease;
				if (a <= 0.01) continue;
				const x = cx + v.x * r;
				const y = cy - v.y * r - (still ? 0 : (age / 1000) * 3 * unit);
				fx!.globalAlpha = Math.min(1, a * (p.blur ? 0.55 : 1));
				if (p.dot) {
					const s = 13 * unit * p.size;
					fx!.drawImage(spark, x - s, y - s, s * 2, s * 2);
				} else {
					const sw = 27 * unit * p.size;
					const sh = sw * (128 / 96);
					fx!.drawImage(p.blur ? soft : sharp, x - sw / 2, y - sh / 2, sw, sh);
				}
			}
			fx!.globalAlpha = 1;
		}

		function frame(now: number) {
			raf = 0;
			if (!visible) return;
			draw(now - start);
			if (!reduced()) raf = requestAnimationFrame(frame);
		}

		function kick() {
			if (!raf && visible && loaded) raf = requestAnimationFrame(frame);
		}

		const img = new Image();
		img.decoding = 'async';
		img.src = '/hero/land.png';
		img.onload = () => {
			gl.bindTexture(gl.TEXTURE_2D, tex);
			gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
			loaded = true;
			start = performance.now();
			ready = true;
			resize();
			kick();
		};
		img.onerror = () => (fallback = true);

		const ro = new ResizeObserver(() => {
			if (!loaded) return;
			resize();
			if (reduced()) draw(frozen);
			kick();
		});
		ro.observe(scene);

		const io = new IntersectionObserver(([entry]) => {
			visible = entry.isIntersecting;
			kick();
		});
		io.observe(scene);

		const onMotion = () => {
			if (!loaded) return;
			frozen = performance.now() - start;
			draw(frozen);
			kick();
		};
		motionQuery.addEventListener('change', onMotion);
		const mo = new MutationObserver(onMotion);
		mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-motion'] });

		const onLost = (e: Event) => {
			e.preventDefault();
			fallback = true;
		};
		gl_canvas.addEventListener('webglcontextlost', onLost);

		return () => {
			cancelAnimationFrame(raf);
			ro.disconnect();
			io.disconnect();
			mo.disconnect();
			motionQuery.removeEventListener('change', onMotion);
			gl_canvas.removeEventListener('webglcontextlost', onLost);
			gl.getExtension('WEBGL_lose_context')?.loseContext();
		};
	});
</script>

<div class="scene" class:ready class:fallback bind:this={scene} aria-hidden="true">
	<canvas class="layer" bind:this={gl_canvas}></canvas>
	<canvas class="layer" bind:this={fx_canvas}></canvas>
	{#if fallback}<img class="layer" src="/hero/globe.webp" alt="" />{/if}
	<noscript><img class="layer" src="/hero/globe.webp" alt="" /></noscript>
</div>

<style>
	.scene {
		position: relative;
		aspect-ratio: 1;
		pointer-events: none;
	}
	.layer {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		display: block;
	}
	canvas.layer {
		opacity: 0;
		transition: opacity 900ms ease;
	}
	.ready canvas.layer {
		opacity: 1;
	}
	.fallback canvas.layer {
		display: none;
	}
</style>
