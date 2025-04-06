void main() {
    vec3 normal = normalize(norm);
    vec3 light_direction = normalize(lightPosition - pos);
    float normal_amount = dot(normal, light_direction);
    vec3 u = normalize(light_direction - normal_amount * normal);
    vec3 v = cross(normal, u);
    vec3 direction = cos(orientationOffset) * u + sin(orientationOffset) * v;
    const float eps = 0.001;
    vec4 pp_clip = viewProjectionMatrix * vec4(pos + eps * direction, 1.0f);
    vec4 pm_clip = viewProjectionMatrix * vec4(pos - eps * direction, 1.0f);
    vec2 dir_screen = pp_clip.xy / pp_clip.w - pm_clip.xy / pm_clip.w;

    // When computing the orientation, scale the y component by -1 to compensate for
    // having to flip the image horizontally. While in major image formats, the origin is
    // assumed to be at the top-left, Blender places the origin at the bottom-left for
    // its 2D image pipeline.
    float orientation = atan(-dir_screen.y, dir_screen.x);
    orientation = isnan(orientation) ? 0.0 : orientation;

    float depth = length(pos - cameraPosition);

    FragColor = vec2(orientation, depth);
}
