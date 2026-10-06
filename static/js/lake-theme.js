/**
 * Pristine Deep-Water Lake Live Background Engine
 * High Performance HTML5 2D Canvas Theme
 */

(function () {
    const canvas = document.createElement('canvas');
    canvas.id = 'lake-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-10';
    canvas.style.pointerEvents = 'none';
    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d', { alpha: false });

    let width = 0;
    let height = 0;
    let time = 0;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    // Mouse Tracking
    const mouse = { x: -1000, y: -1000, targetX: -1000, targetY: -1000, active: false };
    const mouseTrail = [];
    const maxTrailPoints = 25;

    window.addEventListener('mousemove', (e) => {
        mouse.targetX = e.clientX;
        mouse.targetY = e.clientY;
        if (!mouse.active) {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
            mouse.active = true;
        }

        // Add trail node
        mouseTrail.push({
            x: e.clientX,
            y: e.clientY,
            radius: 4,
            maxRadius: 35 + Math.random() * 20,
            alpha: 0.6,
            decay: 0.02 + Math.random() * 0.01
        });

        if (mouseTrail.length > maxTrailPoints) {
            mouseTrail.shift();
        }
    });

    window.addEventListener('mouseleave', () => {
        mouse.active = false;
    });

    // Click Shockwaves & Micro-Droplets
    const shockwaves = [];
    const droplets = [];

    window.addEventListener('click', (e) => {
        const cx = e.clientX;
        const cy = e.clientY;

        // Radial Shockwave Pulse
        shockwaves.push({
            x: cx,
            y: cy,
            radius: 5,
            maxRadius: 180 + Math.random() * 60,
            lineWidth: 6,
            alpha: 0.95
        });
        shockwaves.push({
            x: cx,
            y: cy,
            radius: 2,
            maxRadius: 120 + Math.random() * 40,
            lineWidth: 3,
            alpha: 0.8
        });

        // Fading Blue Micro-Droplets
        const count = 24 + Math.floor(Math.random() * 12);
        for (let i = 0; i < count; i++) {
            const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.4;
            const speed = 2.5 + Math.random() * 5.5;
            droplets.push({
                x: cx,
                y: cy,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                radius: 1.5 + Math.random() * 2.2,
                alpha: 0.9,
                drag: 0.94 + Math.random() * 0.03,
                buoyancy: -0.05 - Math.random() * 0.05
            });
        }
    });

    // Floating Particles (Deep currents)
    const particleCount = 45;
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            radius: 1 + Math.random() * 2.5,
            baseAlpha: 0.2 + Math.random() * 0.5,
            pulseSpeed: 0.01 + Math.random() * 0.02,
            pulsePhase: Math.random() * Math.PI * 2,
            speedY: -0.2 - Math.random() * 0.4,
            swayFreq: 0.008 + Math.random() * 0.012,
            swayAmp: 0.5 + Math.random() * 1.2,
            offset: Math.random() * 1000
        });
    }

    // Deep Lake Caustic & Wave Simulation
    function render() {
        time += 0.015;

        // Background Deep Blue Gradient (#0D47A1 near top to #051329 at bottom)
        const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
        bgGradient.addColorStop(0, '#0D47A1');
        bgGradient.addColorStop(0.4, '#0A2E66');
        bgGradient.addColorStop(1, '#051329');
        ctx.fillStyle = bgGradient;
        ctx.fillRect(0, 0, width, height);

        // Smooth Mouse Interpolation
        if (mouse.active) {
            mouse.x += (mouse.targetX - mouse.x) * 0.15;
            mouse.y += (mouse.targetY - mouse.y) * 0.15;
        }

        // Layered Caustic Light Patterns & Deep Wave Curves
        ctx.save();
        ctx.globalCompositeOperation = 'screen';

        const waveLayers = [
            { color: 'rgba(0, 229, 255, 0.12)', speed: 0.7, amp: 28, freq: 0.004, yOffset: height * 0.25 },
            { color: 'rgba(0, 229, 255, 0.09)', speed: 1.1, amp: 40, freq: 0.003, yOffset: height * 0.45 },
            { color: 'rgba(128, 216, 255, 0.07)', speed: 0.5, amp: 20, freq: 0.006, yOffset: height * 0.65 },
            { color: 'rgba(0, 229, 255, 0.05)', speed: 0.9, amp: 35, freq: 0.0025, yOffset: height * 0.85 }
        ];

        waveLayers.forEach((layer) => {
            ctx.beginPath();
            ctx.strokeStyle = layer.color;
            ctx.lineWidth = 3;

            for (let x = 0; x <= width; x += 15) {
                // Layered sine/cosine compound water math
                const wave1 = Math.sin(x * layer.freq + time * layer.speed) * layer.amp;
                const wave2 = Math.cos(x * layer.freq * 1.6 - time * layer.speed * 0.8) * (layer.amp * 0.5);
                const y = layer.yOffset + wave1 + wave2;

                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
        });

        // Caustic Light Rays / Shimmer Webs
        const causticCount = 6;
        for (let i = 0; i < causticCount; i++) {
            const cx = width * (0.15 + 0.14 * i) + Math.sin(time * 0.8 + i) * 60;
            const cy = height * 0.35 + Math.cos(time * 0.6 + i * 2) * 50;
            const rad = 120 + Math.sin(time + i) * 40;

            const radialGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad);
            radialGrad.addColorStop(0, 'rgba(0, 229, 255, 0.12)');
            radialGrad.addColorStop(0.5, 'rgba(0, 229, 255, 0.04)');
            radialGrad.addColorStop(1, 'rgba(0, 229, 255, 0)');

            ctx.fillStyle = radialGrad;
            ctx.beginPath();
            ctx.arc(cx, cy, rad, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();

        // Render & Update Floating Particles
        ctx.save();
        particles.forEach((p) => {
            p.y += p.speedY;
            p.x += Math.sin(time * 2 + p.offset) * p.swayAmp * 0.3;

            if (p.y < -10) {
                p.y = height + 10;
                p.x = Math.random() * width;
            }

            p.pulsePhase += p.pulseSpeed;
            const currentAlpha = p.baseAlpha + Math.sin(p.pulsePhase) * 0.15;

            // Particle Glow
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 229, 255, ${Math.max(0, currentAlpha)})`;
            ctx.shadowColor = '#00E5FF';
            ctx.shadowBlur = 6;
            ctx.fill();
        });
        ctx.restore();

        // Mouse Ripples & Glowing Trail
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        for (let i = mouseTrail.length - 1; i >= 0; i--) {
            const t = mouseTrail[i];
            t.radius += (t.maxRadius - t.radius) * 0.08;
            t.alpha -= t.decay;

            if (t.alpha <= 0) {
                mouseTrail.splice(i, 1);
                continue;
            }

            ctx.beginPath();
            ctx.arc(t.x, t.y, t.radius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(0, 229, 255, ${t.alpha * 0.7})`;
            ctx.lineWidth = 2;
            ctx.shadowColor = '#00E5FF';
            ctx.shadowBlur = 10;
            ctx.stroke();
        }

        // Mouse Hover Liquid Aura
        if (mouse.active) {
            const auraGrad = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 80);
            auraGrad.addColorStop(0, 'rgba(0, 229, 255, 0.25)');
            auraGrad.addColorStop(0.5, 'rgba(0, 229, 255, 0.08)');
            auraGrad.addColorStop(1, 'rgba(0, 229, 255, 0)');

            ctx.fillStyle = auraGrad;
            ctx.beginPath();
            ctx.arc(mouse.x, mouse.y, 80, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();

        // Click Shockwaves
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        for (let i = shockwaves.length - 1; i >= 0; i--) {
            const sw = shockwaves[i];
            sw.radius += (sw.maxRadius - sw.radius) * 0.12 + 1.5;
            sw.alpha -= 0.025;

            if (sw.alpha <= 0 || sw.radius >= sw.maxRadius) {
                shockwaves.splice(i, 1);
                continue;
            }

            ctx.beginPath();
            ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(0, 229, 255, ${Math.max(0, sw.alpha)})`;
            ctx.lineWidth = sw.lineWidth * (sw.alpha);
            ctx.shadowColor = '#00E5FF';
            ctx.shadowBlur = 15;
            ctx.stroke();
        }
        ctx.restore();

        // Click Micro-Droplets
        ctx.save();
        for (let i = droplets.length - 1; i >= 0; i--) {
            const d = droplets[i];
            d.x += d.vx;
            d.y += d.vy;
            d.vx *= d.drag;
            d.vy *= d.drag;
            d.vy += d.buoyancy; // Float upward slightly
            d.alpha -= 0.02;

            if (d.alpha <= 0) {
                droplets.splice(i, 1);
                continue;
            }

            ctx.beginPath();
            ctx.arc(d.x, d.y, d.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(128, 216, 255, ${Math.max(0, d.alpha)})`;
            ctx.shadowColor = '#00E5FF';
            ctx.shadowBlur = 8;
            ctx.fill();
        }
        ctx.restore();

        requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
})();
