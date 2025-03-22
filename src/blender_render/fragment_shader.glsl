void main() {
    float depth = length(pos);

    vec3 lightDirection = normalize(lightPosition - pos);
    vec3 normal = normalize(norm);
    float normal_amount = dot(normal, lightDirection);
    float diffuse = max(normal_amount, 0.0f);

    vec3 u = normalize(lightDirection - normal_amount * normal);
    const float eps = 1.0e-6f;
    vec3 b = pos + eps * u;
    vec3 a = pos - eps * u;
    vec2 dir = b.xy - a.xy;
    float orientation = atan(dir.y, dir.x);

    FragColor = vec4(diffuse, orientation, depth, 1.0f);
}
