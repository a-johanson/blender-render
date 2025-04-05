void main() {
    vec3 normal = normalize(norm);
    vec3 light_direction = normalize(lightPosition - pos);
    float normal_amount = dot(normal, light_direction);
    vec3 u = normalize(light_direction - normal_amount * normal);
    vec3 v = cross(normal, u);
    vec3 direction = cos(orientationOffset) * u + sin(orientationOffset) * v;
    const float eps = 0.001;
    vec3 pp = pos + eps * direction;
    vec3 pm = pos - eps * direction;
    vec4 pp_clip = viewProjectionMatrix * vec4(pp, 1.0f);
    vec4 pm_clip = viewProjectionMatrix * vec4(pm, 1.0f);
    vec2 dir_screen = pp_clip.xy / pp_clip.w - pm_clip.xy / pm_clip.w;
    float orientation = atan(dir_screen.y, dir_screen.x);
    orientation = isnan(orientation) ? 0.0 : orientation;

    float depth = length(pos - cameraPosition);

    FragColor = vec2(orientation, depth);
}
