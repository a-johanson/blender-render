void main() {
    vec3 lightDirection = normalize(lightPosition - pos);
    vec3 normal = normalize(norm);
    float normal_amount = dot(normal, lightDirection);
    float diffuse = max(normal_amount, 0.0f);

    vec3 u = lightDirection - normal_amount * normal;
    float orientation = atan(u.y, u.x);

    float depth = length(pos);

    FragColor = vec4(diffuse, orientation, depth, 1.0f);
}
