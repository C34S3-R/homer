
#!/usr/bin/env python3
"""
redeploy.py - Rebuild a Docker image and replace the running container.

Steps:
  1. Build the new image (old container keeps running if the build fails)
  2. Stop the old container (if it exists)
  3. Remove the old container
  4. Run a new container from the fresh image
  5. (optional) Prune dangling images left behind by the rebuild

Examples:
  python redeploy.py --name myapp -p 8000:8000
  python redeploy.py --name myapp -p 80:5000 -e-file .env -v ./data:/app/data --prune
  python redeploy.py --name myapp --context ./backend --dockerfile Dockerfile.prod -p 8000:8000
"""

import argparse
import shutil
import subprocess
import sys


def run(cmd, check=True, capture=False):
    """Run a command, echoing it first."""
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=capture)
    if check and result.returncode != 0:
        if capture:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
        sys.exit(f"Command failed with exit code {result.returncode}")
    return result


def container_exists(name):
    """Return True if a container (running or stopped) with this name exists."""
    result = run(
        ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"],
        capture=True,
    )
    return name in result.stdout.split()


def main():
    p = argparse.ArgumentParser(description="Rebuild image and replace Docker container.")
    p.add_argument("--name", required=True, help="Container name")
    p.add_argument("--image", help="Image name (defaults to the container name)")
    p.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    p.add_argument("--context", default=".", help="Build context directory (default: .)")
    p.add_argument("--dockerfile", help="Path to Dockerfile (default: <context>/Dockerfile)")
    p.add_argument("-p", "--port", action="append", default=[], help="Port mapping, e.g. 8000:8000 (repeatable)")
    p.add_argument("-v", "--volume", action="append", default=[], help="Volume mount, e.g. ./data:/app/data (repeatable)")
    p.add_argument("-e", "--env", action="append", default=[], help="Env var, e.g. KEY=value (repeatable)")
    p.add_argument("--env-file", help="Path to an env file")
    p.add_argument("--network", help="Docker network to attach to")
    p.add_argument("--restart", default="unless-stopped", help="Restart policy (default: unless-stopped)")
    p.add_argument("--no-cache", action="store_true", help="Build without using the cache")
    p.add_argument("--prune", action="store_true", help="Remove dangling images after deploying")
    p.add_argument("--foreground", action="store_true", help="Run attached instead of detached")
    args = p.parse_args()

    if not shutil.which("docker"):
        sys.exit("Docker not found. Is it installed and on your PATH?")

    image = f"{args.image or args.name}:{args.tag}"

    # 1. Build first, so a broken build never takes down the running container
    print(f"==> Building image {image}")
    build_cmd = ["docker", "build", "-t", image]
    if args.dockerfile:
        build_cmd += ["-f", args.dockerfile]
    if args.no_cache:
        build_cmd.append("--no-cache")
    build_cmd.append(args.context)
    run(build_cmd)

    # 2 & 3. Stop and remove the old container
    if container_exists(args.name):
        print(f"==> Stopping old container '{args.name}'")
        run(["docker", "stop", args.name])
        print(f"==> Removing old container '{args.name}'")
        run(["docker", "rm", args.name])
    else:
        print(f"==> No existing container named '{args.name}', skipping stop/remove")

    # 4. Start the new container
    print(f"==> Starting new container '{args.name}'")
    run_cmd = ["docker", "run", "--name", args.name, "--restart", args.restart]
    if not args.foreground:
        run_cmd.append("-d")
    for port in args.port:
        run_cmd += ["-p", port]
    for vol in args.volume:
        run_cmd += ["-v", vol]
    for env in args.env:
        run_cmd += ["-e", env]
    if args.env_file:
        run_cmd += ["--env-file", args.env_file]
    if args.network:
        run_cmd += ["--network", args.network]
    run_cmd.append(image)
    run(run_cmd)

    # 5. Cleanup
    if args.prune:
        print("==> Pruning dangling images")
        run(["docker", "image", "prune", "-f"])

    print(f"\nDone. '{args.name}' is now running the latest build.")
    print(f"Logs: docker logs -f {args.name}")


if __name__ == "__main__":
    main()
