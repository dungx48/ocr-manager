import decouple
import sys
import uvicorn

if __name__ == "__main__":
    env_file = decouple.RepositoryEnv(sys.argv[1])
    
    decouple.config = decouple.Config(env_file)
    port = int(decouple.config('PORT'))
    sys.path.insert(0, '..')
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=False)